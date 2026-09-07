#!/usr/bin/env python3
"""
Minimal diagnostic logistic regression trainer (no sklearn dependency).
Reads manifest.json, fits logistic regression via numpy gradient descent,
writes metrics.json, report.html, predictions.json, and updates manifest.model_spec.
"""
import argparse, csv, hashlib, json, sys
from pathlib import Path

try:
    import numpy as np
except Exception:
    print("FAIL: numpy is required for diagnostic_logistic trainer")
    sys.exit(1)


def load_json(path):
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def read_data(path, feature_cols, outcome_col):
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            x = [float(row[c]) for c in feature_cols]
            y = float(row[outcome_col])
            rows.append((x, y))
    return rows


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def fit_logistic(X, y, lr=0.5, epochs=800, l2=1e-3, seed=42):
    rng = np.random.default_rng(seed)
    n, p = X.shape
    w = rng.normal(scale=0.01, size=(p,))
    b = 0.0
    for _ in range(epochs):
        logit = X @ w + b
        p_vec = sigmoid(logit)
        grad_w = (X.T @ (p_vec - y)) / n + l2 * w
        grad_b = float(np.mean(p_vec - y))
        w -= lr * grad_w
        b -= lr * grad_b
    return w, b


def compute_metrics(y_true, probs, threshold=0.5):
    tp = sum(1 for y, p in zip(y_true, probs) if p >= threshold and y == 1)
    fp = sum(1 for y, p in zip(y_true, probs) if p >= threshold and y == 0)
    tn = sum(1 for y, p in zip(y_true, probs) if p < threshold and y == 0)
    fn = sum(1 for y, p in zip(y_true, probs) if p < threshold and y == 1)
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    ppv = tp / (tp + fp) if (tp + fp) else 0.0
    npv = tn / (tn + fn) if (tn + fn) else 0.0
    # crude AUC via ranking
    pos = [p for y, p in zip(y_true, probs) if y == 1]
    neg = [p for y, p in zip(y_true, probs) if y == 0]
    auc = 0.5
    if pos and neg:
        concordant = 0
        for pi in pos:
            for ni in neg:
                if pi > ni:
                    concordant += 1
                elif pi == ni:
                    concordant += 0.5
        auc = concordant / (len(pos) * len(neg))
    brier = sum((p - y) ** 2 for y, p in zip(y_true, probs)) / len(y_true)
    return {
        'auc': round(auc, 4),
        'sensitivity': round(sens, 4),
        'specificity': round(spec, 4),
        'ppv': round(ppv, 4),
        'npv': round(npv, 4),
        'brier': round(brier, 4),
        'c_index': None,
        'time_dependent_auc': None,
        'hr': None,
        'or': None,
        'i2': None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--threshold', type=float, default=0.5)
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    base_dir = manifest_path.parent
    m = load_json(manifest_path)

    input_files = m.get('input_files', []) or []
    if not input_files:
        print("FAIL: input_files missing")
        sys.exit(1)
    data_path = (base_dir / input_files[0]['path']).resolve()
    if not data_path.exists():
        print(f"FAIL: data file not found: {data_path}")
        sys.exit(1)

    col_map = m.get('column_map', {}) or {}
    outcome_col = col_map.get('outcome')
    id_col = col_map.get('id', 'id')
    with open(data_path, newline='', encoding='utf-8') as f:
        header = next(csv.reader(f))
    feature_cols = [c for c in header if c not in {'id', outcome_col, col_map.get('time',''), col_map.get('event','')}]
    feature_cols = [c for c in feature_cols if c]
    if not feature_cols or not outcome_col:
        print("FAIL: cannot infer feature columns or outcome")
        sys.exit(1)

    rows = read_data(data_path, feature_cols, outcome_col)
    ids = []
    with open(data_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row[id_col])
    X = np.array([[r[0] for r in rows]], dtype=float).reshape(len(rows), -1)
    y = np.array([r[1] for r in rows], dtype=float)

    # split into train/val using manifest split_manifest
    split = m.get('split_manifest', {}) or {}
    train_ids = set(split.get('train', []))
    val_ids = set(split.get('validation', []) or split.get('test', []) or [])
    train_idx = [i for i, id_ in enumerate(ids) if id_ in train_ids]
    val_idx = [i for i, id_ in enumerate(ids) if id_ in val_ids]
    if not train_idx or not val_idx:
        # fallback: first 80% train, rest val
        k = max(1, int(0.8 * len(rows)))
        train_idx = list(range(k))
        val_idx = list(range(k, len(rows)))

    X_train = X[train_idx]
    y_train = y[train_idx]
    X_val = X[val_idx]
    y_val = y[val_idx]

    # standardize features using train stats
    means = X_train.mean(axis=0)
    stds = X_train.std(axis=0)
    stds[stds == 0] = 1.0
    X_train = (X_train - means) / stds
    X_val = (X_val - means) / stds

    w, b = fit_logistic(X_train, y_train)
    val_probs = sigmoid(X_val @ w + b).tolist()
    train_probs = sigmoid(X_train @ w + b).tolist()
    metrics = compute_metrics(y_val.tolist(), val_probs, threshold=args.threshold)

    # persist deidentified prediction artifacts (no patient IDs)
    data_path_for_hash = base_dir / input_files[0]['path']
    data_hash = sha256_file(data_path_for_hash) if data_path_for_hash.exists() else ''
    model_spec = m.get('model_spec', {}) or {}
    model_spec_for_hash = {k: v for k, v in model_spec.items() if k != 'preprocessing'}
    model_hash = hashlib.sha256(json.dumps(model_spec_for_hash, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    predictions = {
        'split': 'validation',
        'threshold': args.threshold,
        'data_hash': data_hash,
        'model_hash': model_hash,
        'n_samples': len(val_idx),
        'y_true': [int(v) for v in y_val.tolist()],
        'y_prob': [round(float(p), 6) for p in val_probs],
        'y_pred': [int(p >= args.threshold) for p in val_probs],
    }
    pred_path = base_dir / 'predictions.json'
    save_json(pred_path, predictions)

    train_predictions = {
        'split': 'train',
        'threshold': args.threshold,
        'data_hash': data_hash,
        'model_hash': model_hash,
        'n_samples': len(train_idx),
        'y_true': [int(v) for v in y_train.tolist()],
        'y_prob': [round(float(p), 6) for p in train_probs],
        'y_pred': [int(p >= args.threshold) for p in train_probs],
    }
    train_pred_path = base_dir / 'predictions_train.json'
    save_json(train_pred_path, train_predictions)

    metrics_path = base_dir / 'metrics.json'
    save_json(metrics_path, metrics)

    # update manifest model_spec
    model_spec = m.get('model_spec', {}) or {}
    model_spec['features'] = feature_cols
    model_spec['coefficients'] = [round(float(c), 6) for c in w.tolist()]
    model_spec['intercept'] = round(float(b), 6)
    model_spec['preprocessing'] = {'standardize': True, 'missing': 'omit'}
    m['model_spec'] = model_spec
    m['metrics'] = metrics
    # ensure prediction artifacts are referenced in manifest
    artifacts = m.get('artifacts', []) or []
    for extra in ['predictions.json', 'predictions_train.json']:
        if extra not in artifacts:
            artifacts.append(extra)
    m['artifacts'] = artifacts
    save_json(manifest_path, m)

    # write report.html
    html = f'''<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><title>Diagnostic Report</title></head><body>
<h1>Diagnostic Model Report</h1>
<!-- DEMO_WATERMARK_START -->
<div class="demo">⚠ DEMO / 模拟数据声明：本报告为模拟数据演示，不得用于真实临床场景或学术发表。</div>
<!-- DEMO_WATERMARK_END -->
<table border="1" cellpadding="4">
<tr><th>Metric</th><th>Value</th></tr>
'''
    for k in ['auc','sensitivity','specificity','ppv','npv','brier']:
        html += f'<tr><td>{k}</td><td>{metrics[k]}</td></tr>\n'
    html += '</table>'
    html += '<h2>Figures</h2><div id="figures"><p>See <code>plots/</code> directory for evaluation figures (ROC, PR, calibration).</p><p>Figure manifest: <code>figure_manifest.json</code></p></div>'
    html += '</body></html>'
    (base_dir / 'report.html').write_text(html, encoding='utf-8')
    print('wrote', metrics_path)
    print('wrote', base_dir / 'report.html')
    print('wrote', pred_path)
    print('wrote', train_pred_path)

if __name__ == '__main__':
    main()
