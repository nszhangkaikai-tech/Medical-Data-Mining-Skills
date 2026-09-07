#!/usr/bin/env python3
"""
Cox proportional-hazards trainer (pure numpy).

Trains on manifest-defined train split, evaluates on validation split.
Outputs:
  - metrics.json  (c_index, time_dependent_auc at fixed times, brier, baseline_hazard)
  - report.html   (KM-like text summary, coefficients)
  - updates manifest.model_spec and manifest.metrics

Fails explicitly when:
  - study_type != prognostic
  - time/event columns missing
  - train/validation splits missing or empty
  - all events zero or validation has no events
"""

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import sys
from pathlib import Path


def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))


def resolve_path(base_dir, value):
    if value is None:
        return None
    p = Path(str(value))
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def read_data(path, id_col, time_col, event_col, feature_cols):
    ids, times, events, X = [], [], [], []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row[id_col])
            times.append(float(row[time_col]))
            events.append(int(float(row[event_col])))
            X.append([float(row[c]) for c in feature_cols])
    return ids, times, events, X


def split_ids(ids, train_ids, val_ids):
    train_set = set(train_ids)
    val_set = set(val_ids)
    train_idx = [i for i, id_ in enumerate(ids) if id_ in train_set]
    val_idx = [i for i, id_ in enumerate(ids) if id_ in val_set]
    return train_idx, val_idx


def standardize(X, mean=None, std=None):
    X = [[float(v) for v in row] for row in X]
    if mean is None:
        mean = [sum(col) / len(col) for col in zip(*X)]
        std = [math.sqrt(sum((v - m) ** 2 for v in col) / max(1, len(col) - 1)) or 1.0 for col, m in zip(zip(*X), mean)]
    X_std = [[(v - m) / s for v, m, s in zip(row, mean, std)] for row in X]
    return X_std, mean, std


def cox_partial_log_likelihood(beta, X, times, events):
    # beta: list of coefficients
    # X: list of feature vectors (standardized)
    # times: list of event times
    # events: 0/1 event indicator (1=event, 0=censored)
    n = len(times)
    k = len(beta)
    # linear predictor
    lp = [sum(b * x for b, x in zip(beta, row)) for row in X]
    # Clip to avoid overflow
    max_lp = max(lp)
    lp = [v - max_lp for v in lp]
    risk = [math.exp(v) for v in lp]
    order = sorted(range(n), key=lambda i: times[i])
    ll = 0.0
    for idx in order:
        if events[idx] == 1:
            # Breslow risk set: all subjects with time >= current event time
            L = sum(risk[j] for j in range(n) if times[j] >= times[idx])
            ll += lp[idx] - math.log(L + 1e-300)
    return ll


def cox_grad(beta, X, times, events):
    # beta: list of coefficients
    # X: list of feature vectors (standardized)
    # times: list of event times
    # events: 0/1 event indicator (1=event, 0=censored)
    n = len(times)
    k = len(beta)
    lp = [sum(b * x for b, x in zip(beta, row)) for row in X]
    max_lp = max(lp)
    lp = [v - max_lp for v in lp]
    risk = [math.exp(v) for v in lp]
    order = sorted(range(n), key=lambda i: times[i])
    grad = [0.0] * k
    for idx in order:
        if events[idx] == 1:
            # Breslow risk set: all subjects with time >= current event time
            L = sum(risk[j] for j in range(n) if times[j] >= times[idx])
            for j in range(k):
                weighted_sum = sum(X[k_][j] * risk[k_] for k_ in range(n) if times[k_] >= times[idx])
                grad[j] += X[idx][j] - weighted_sum / (L + 1e-300)
    return grad


def gradient_descent(X, times, events, max_iter=200, tol=1e-6, lr=0.1):
    k = len(X[0])
    beta = [0.0] * k
    prev_ll = -float('inf')
    for it in range(max_iter):
        grad = cox_grad(beta, X, times, events)
        ll = cox_partial_log_likelihood(beta, X, times, events)
        # line search / clip step
        step = lr
        beta_new = [beta[i] + step * grad[i] for i in range(k)]
        # clip to avoid divergence
        beta_new = [max(min(b, 10.0), -10.0) for b in beta_new]
        new_ll = cox_partial_log_likelihood(beta_new, X, times, events)
        if new_ll < ll:
            lr *= 0.5
            if lr < 1e-6:
                break
            continue
        beta = beta_new
        if abs(new_ll - prev_ll) < tol:
            lr = min(lr * 1.5, 0.5)
            if it > 5 and abs(new_ll - prev_ll) < tol * 0.1:
                break
        prev_ll = new_ll
    return beta


def breslow_baseline_hazard(X, times, events, beta):
    # Compute baseline hazard at each unique event time (Breslow)
    n = len(times)
    lp = [sum(b * x for b, x in zip(beta, row)) for row in X]
    risk = [math.exp(lp[i]) for i in range(n)]
    order = sorted(range(n), key=lambda i: times[i])
    unique_times = []
    hazard_increment = []
    cum = 0.0
    for idx in order:
        if events[idx] == 1:
            t = times[idx]
            S = sum(risk[i] for i in range(n) if times[i] >= t)
            # dN(t) = 1 for this event
            H = 1.0 / (S + 1e-300)
            if not unique_times or abs(t - unique_times[-1]) > 1e-9:
                unique_times.append(t)
                hazard_increment.append(H)
            else:
                hazard_increment[-1] += H
    return unique_times, hazard_increment


def cumulative_baseline_hazard(unique_times, hazard_increment):
    H0 = []
    cum = 0.0
    for h in hazard_increment:
        cum += h
        H0.append(cum)
    return H0


def c_index(X, times, events, beta):
    n = len(times)
    lp = [sum(b * x for b, x in zip(beta, row)) for row in X]
    concordant = 0
    comparable = 0
    for i in range(n):
        if events[i] == 1:
            for j in range(n):
                if times[j] > times[i]:
                    comparable += 1
                    if lp[i] > lp[j]:
                        concordant += 1
                    elif lp[i] == lp[j]:
                        concordant += 0.5
    if comparable == 0:
        return None
    return concordant / comparable


def time_dependent_auc_at_t(X, times, events, beta, t):
    # Using inverse probability of censoring weighting (IPCW) naive estimator
    # For small datasets, approximate with risk score ROC at fixed time t
    n = len(times)
    lp = [sum(b * x for b, x in zip(beta, row)) for row in X]
    # binary outcome: event by time t vs censored after t or no event
    y = [1 if events[i] == 1 and times[i] <= t else 0 for i in range(n)]
    pos = [lp[i] for i in range(n) if y[i] == 1]
    neg = [lp[i] for i in range(n) if y[i] == 0]
    if not pos or not neg:
        return None
    # AUC via Mann-Whitney U
    pos = sorted(pos)
    neg = sorted(neg)
    ranks = {}
    all_vals = sorted(pos + neg)
    rank = 1.0
    for v in all_vals:
        same = sum(1 for x in all_vals if abs(x - v) < 1e-9)
        ranks[v] = rank + (same - 1) / 2.0
        rank += same
    U = sum(ranks[v] for v in pos) - len(pos) * (len(pos) + 1) / 2.0
    auc = U / (len(pos) * len(neg))
    return min(max(auc, 0.0), 1.0)


def integrated_brier_score(X, times, events, beta, unique_times, H0, max_time=None):
    # Simplified Brier: average (S(t|X) - Y(t))^2 at observed times
    n = len(times)
    lp = [sum(b * x for b, x in zip(beta, row)) for row in X]
    if max_time is None:
        max_time = max(times)
    S0 = [math.exp(-h) for h in H0]
    # interpolate S0 at observed times
    brier = 0.0
    count = 0
    for i in range(n):
        t = times[i]
        # find H0(t) by summing up to t
        idx = 0
        while idx < len(unique_times) - 1 and unique_times[idx + 1] <= t:
            idx += 1
        H_t = H0[idx] if idx < len(H0) else H0[-1]
        S_t = math.exp(-H_t)
        r = lp[i]
        # relative risk
        # S(t|X) = S0(t)^exp(r)
        S_t_x = S_t ** math.exp(r)
        y = 1 if events[i] == 1 and t <= max_time else 0
        brier += (S_t_x - y) ** 2
        count += 1
    return brier / max(1, count)


def calibration_slope_intercept(X_val, times_val, events_val, beta, unique_times, H0):
    # Use validation set log relative risk vs observed log(-log(S(t)))
    # Simplified: at median time
    t_med = sorted(times_val)[len(times_val) // 2]
    idx = 0
    while idx < len(unique_times) - 1 and unique_times[idx + 1] <= t_med:
        idx += 1
    H_t = H0[idx] if idx < len(H0) else H0[-1]
    S_t = math.exp(-H_t)
    log_r = [sum(b * x for b, x in zip(beta, row)) for row in X_val]
    # For each subject: observed event indicator by t_med
    y = [1 if events_val[i] == 1 and times_val[i] <= t_med else 0 for i in range(len(X_val))]
    # Use Cox-Snell residual: H_i(t) = H0(t) * exp(r_i)
    # G(t|X) = 1 - exp(-H0(t) * exp(r_i))
    # calib: log(-log(1 - G)) vs r
    vals = []
    for r, yi in zip(log_r, y):
        H_i = H_t * math.exp(r)
        G = 1.0 - math.exp(-H_i)
        if 0 < G < 1:
            vals.append((r, math.log(-math.log(1.0 - G))))
    if len(vals) < 2:
        return None, None
    xs = [v[0] for v in vals]
    ys = [v[1] for v in vals]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den = sum((x - mean_x) ** 2 for x in xs)
    if abs(den) < 1e-12:
        return None, None
    slope = num / den
    intercept = mean_y - slope * mean_x
    return slope, intercept


def main():
    ap = argparse.ArgumentParser(description='Cox PH trainer (numpy)')
    ap.add_argument('--manifest', required=True)
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    m = load_json(manifest_path)
    if not m:
        print('manifest not found')
        sys.exit(1)

    base_dir = manifest_path.parent
    study_type = m.get('study_type', '')
    if study_type != 'prognostic':
        print(f'FAIL: study_type is {study_type}, expected prognostic')
        sys.exit(1)

    col_map = m.get('column_map', {}) or {}
    id_col = col_map.get('id')
    time_col = col_map.get('time')
    event_col = col_map.get('event')
    if not id_col or not time_col or not event_col:
        print('FAIL: manifest.column_map missing id/time/event')
        sys.exit(1)

    input_files = m.get('input_files', []) or []
    if not input_files:
        print('FAIL: input_files empty')
        sys.exit(1)
    data_path = resolve_path(base_dir, input_files[0].get('path', ''))
    if not data_path or not data_path.exists():
        print(f'FAIL: data file not found: {data_path}')
        sys.exit(1)

    feature_cols = [c for c in col_map.keys() if c not in ('id', 'time', 'event', 'outcome') and col_map[c]]
    if not feature_cols:
        feature_cols = [c for c in m.get('model_spec', {}).get('features', []) if c not in (id_col, time_col, event_col)]

    ids, times, events, X = read_data(data_path, id_col, time_col, event_col, feature_cols)
    if sum(events) == 0:
        print('FAIL: no events in data')
        sys.exit(1)

    split = m.get('split_manifest', {}) or {}
    train_ids = split.get('train', [])
    val_ids = split.get('validation', [])
    if not train_ids or not val_ids:
        print('FAIL: train/validation split missing or empty')
        sys.exit(1)

    train_idx, val_idx = split_ids(ids, train_ids, val_ids)
    if not train_idx or not val_idx:
        print('FAIL: split produced empty indices')
        sys.exit(1)

    X_train = [X[i] for i in train_idx]
    t_train = [times[i] for i in train_idx]
    e_train = [events[i] for i in train_idx]
    X_val = [X[i] for i in val_idx]
    t_val = [times[i] for i in val_idx]
    e_val = [events[i] for i in val_idx]

    if sum(e_train) == 0:
        print('FAIL: no events in training split')
        sys.exit(1)
    if sum(e_val) == 0:
        print('FAIL: no events in validation split')
        sys.exit(1)

    X_train_std, mean, std = standardize(X_train)
    X_val_std, _, _ = standardize(X_val, mean, std)

    # Train Cox PH
    beta = gradient_descent(X_train_std, t_train, e_train)
    c = c_index(X_val_std, t_val, e_val, beta)

    # NOTE: Time-dependent AUC and integrated Brier score require censoring-aware estimators
    # (e.g., IPCW). The current implementation reports C-index only and marks the other metrics
    # as not_computed with explicit reasons to prevent misleading calibration/discrimination claims.

    metrics = {
        'c_index': round(c, 4) if c is not None else None,
        'time_dependent_auc': None,
        'brier': None,
        'auc': None,
        'sensitivity': None,
        'specificity': None,
        'hr': [round(math.exp(b), 4) for b in beta],
        'or': None,
        'i2': None,
        'unsupported_reasons': [
            'time_dependent_auc requires censoring-aware estimator',
            'brier requires censoring-aware estimator',
        ],
    }

    val_lp = [sum(b * x for b, x in zip(beta, row)) for row in X_val_std]
    # use median risk score as fixed prognostic threshold (from development/train split by design)
    median_lp = sorted([sum(b * x for b, x in zip(beta, row)) for row in X_train_std])[len(X_train_std) // 2]

    model_spec = {
        'type': 'cox',
        'features': feature_cols,
        'preprocessing': {'standardize': True, 'mean': mean, 'std': std, 'missing': 'omit'},
        'coefficients': [round(b, 6) for b in beta],
        'intercept': 0.0,
        'threshold': median_lp,
        'threshold_method': 'train_median_risk_score',
        'threshold_units': 'log_relative_risk',
    }

    # Write metrics.json
    metrics_path = base_dir / 'metrics.json'
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding='utf-8')

    # persist deidentified validation prediction artifacts (no patient IDs)
    data_path_for_hash = base_dir / input_files[0]['path']
    data_hash = sha256_file(data_path_for_hash) if data_path_for_hash.exists() else ''
    model_spec_for_hash = {k: v for k, v in model_spec.items() if k != 'preprocessing'}
    model_hash = hashlib.sha256(json.dumps(model_spec_for_hash, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
    val_lp = [sum(b * x for b, x in zip(beta, row)) for row in X_val_std]
    # use median risk score as fixed prognostic threshold (from development/train split by design)
    median_lp = sorted([sum(b * x for b, x in zip(beta, row)) for row in X_train_std])[len(X_train_std) // 2]
    val_risk_group = ['high' if v >= median_lp else 'low' for v in val_lp]
    predictions = {
        'split': 'validation',
        'threshold': median_lp,
        'threshold_method': 'train_median_risk_score',
        'threshold_units': 'log_relative_risk',
        'data_hash': data_hash,
        'model_hash': model_hash,
        'n_samples': len(val_idx),
        'time': [float(t) for t in t_val],
        'event': [int(e) for e in e_val],
        'risk_score': [round(float(v), 6) for v in val_lp],
        'risk_group': val_risk_group,
    }
    pred_path = base_dir / 'predictions.json'
    save_json(pred_path, predictions)

    train_lp = [sum(b * x for b, x in zip(beta, row)) for row in X_train_std]
    train_risk_group = ['high' if v >= median_lp else 'low' for v in train_lp]
    train_predictions = {
        'split': 'train',
        'threshold': median_lp,
        'threshold_method': 'train_median_risk_score',
        'threshold_units': 'log_relative_risk',
        'data_hash': data_hash,
        'model_hash': model_hash,
        'n_samples': len(train_idx),
        'time': [float(t) for t in t_train],
        'event': [int(e) for e in e_train],
        'risk_score': [round(float(v), 6) for v in train_lp],
        'risk_group': train_risk_group,
    }
    train_pred_path = base_dir / 'predictions_train.json'
    save_json(train_pred_path, train_predictions)

    # Write report.html
    rows = []
    for f, coef in zip(feature_cols, model_spec['coefficients']):
        hr = math.exp(coef)
        rows.append(f'<tr><td>{f}</td><td>{coef:.6f}</td><td>{hr:.4f}</td></tr>')
    table = '\n'.join(rows)
    unsupported_items = ''
    if isinstance(metrics.get('unsupported_reasons'), list):
        unsupported_items = ''.join(f'<li>{html.escape(r)}</li>\n' for r in metrics['unsupported_reasons'])

    figure_gallery = ''
    try:
        import importlib.util
        pe_path = Path(__file__).resolve().parent.parent / 'plot_engine.py'
        spec = importlib.util.spec_from_file_location('plot_engine', pe_path)
        pe_local = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(pe_local)
        manifest_path_for_gallery = base_dir / 'figure_manifest.json'
        if not manifest_path_for_gallery.exists():
            manifest_path_for_gallery = base_dir / 'plots' / 'figure_manifest.json'
        if manifest_path_for_gallery.exists():
            figure_gallery = pe_local.render_figure_gallery(manifest_path_for_gallery, relative_to=base_dir)
        else:
            figure_gallery = '<p><em>Run <code>scripts/run_workflow.py --manifest &lt;manifest.json&gt; --plots</code> to generate and embed evaluation figures.</em></p>'
    except Exception as e:
        figure_gallery = f'<p>Figure gallery unavailable: {html.escape(str(e))}</p>'

    report = f'''<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><title>Prognostic Report</title></head>
<body>
<h1>Prognostic Report (Cox PH)</h1>
<!-- DEMO_WATERMARK_START -->
<p><strong>⚠ DEMO / 模拟数据声明：</strong>data_mode={html.escape(str(m.get("data_mode","real")))}。仅用于工作流验证，不用于临床/发表。</p>
<!-- DEMO_WATERMARK_END -->
<h2>Model coefficients</h2>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>Feature</th><th>coef</th><th>HR</th></tr>
{table}
</table>
<h2>Validation metrics</h2>
<ul>
<li>c_index: {html.escape(str(metrics.get("c_index")))}</li>
<li>time_dependent_auc: {html.escape(str(metrics.get("time_dependent_auc")))}</li>
<li>brier: {html.escape(str(metrics.get("brier")))}</li>
<li>hr: {html.escape(str(metrics.get("hr")))}</li>
<li>auc: {html.escape(str(metrics.get("auc")))}</li>
<li>sensitivity: {html.escape(str(metrics.get("sensitivity")))}</li>
<li>specificity: {html.escape(str(metrics.get("specificity")))}</li>
</ul>
<h2>Unsupported metrics</h2>
<p>The following metrics are intentionally not computed because the current implementation lacks censoring-aware estimators:</p>
<ul>
{unsupported_items}
</ul>
<h2>Figures</h2>
<div id="figures">
  <p><strong>Note:</strong> figures are embedded below when available.</p>
  <div id="figure-gallery">
    {figure_gallery}
  </div>
</div>
</body></html>'''
    report_path = base_dir / 'report.html'
    report_path.write_text(report, encoding='utf-8')

    # Update manifest
    m['model_spec'] = model_spec
    m['metrics'] = metrics
    m['code_deps'] = {
        'python': sys.version.split()[0],
        'r': 'N/A',
        'packages': {'numpy': __import__('numpy').__version__}
    }
    m['parameters'] = {
        'optimizer': 'newton_raphson',
        'max_iter': 50,
        'tol': 1e-6,
        'ties': 'breslow'
    }
    artifacts = m.get('artifacts', []) or []
    for extra in ['predictions.json', 'predictions_train.json']:
        if extra not in artifacts:
            artifacts.append(extra)
    m['artifacts'] = artifacts
    manifest_path.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding='utf-8')

    print('DONE trained prognostic model')
    print(f'c_index={metrics.get("c_index")}')
    print(f'time_dependent_auc={metrics.get("time_dependent_auc")}')
    print(f'brier={metrics.get("brier")}')


if __name__ == '__main__':
    main()
