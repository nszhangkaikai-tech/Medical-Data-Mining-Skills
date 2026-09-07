#!/usr/bin/env python3
"""
External validation runner for medical-data-mining skill.

Expects an external CSV with the same column_map as the development manifest.
Outputs external_metrics.json and can update manifest.external_validation.

Usage:
  python3 scripts/external_validation.py \
    --manifest tests/fixtures/compliant_diagnostic/manifest.json \
    --external-data /path/to/external.csv
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

try:
    import numpy as np
except Exception:
    print("FAIL: numpy is required for external_validation")
    sys.exit(1)


def load_json(path):
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def read_diagnostic_data(path, feature_cols, outcome_col, id_col):
    ids = []
    X = []
    y = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row[id_col])
            X.append([float(row[c]) for c in feature_cols])
            y.append(float(row[outcome_col]))
    return ids, np.array(X, dtype=float), np.array(y, dtype=float)


def read_prognostic_data(path, feature_cols, time_col, event_col, id_col):
    ids = []
    X = []
    times = []
    events = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row[id_col])
            X.append([float(row[c]) for c in feature_cols])
            times.append(float(row[time_col]))
            events.append(int(float(row[event_col])))
    return ids, np.array(X, dtype=float), times, events


def compute_diagnostic_metrics(y_true, probs, threshold=0.5):
    tp = sum(1 for y, p in zip(y_true, probs) if p >= threshold and y == 1)
    fp = sum(1 for y, p in zip(y_true, probs) if p >= threshold and y == 0)
    tn = sum(1 for y, p in zip(y_true, probs) if p < threshold and y == 0)
    fn = sum(1 for y, p in zip(y_true, probs) if p < threshold and y == 1)
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    ppv = tp / (tp + fp) if (tp + fp) else 0.0
    npv = tn / (tn + fn) if (tn + fn) else 0.0
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
        'auc': round(float(auc), 4),
        'sensitivity': round(float(sens), 4),
        'specificity': round(float(spec), 4),
        'ppv': round(float(ppv), 4),
        'npv': round(float(npv), 4),
        'brier': round(float(brier), 4),
    }


def compute_prognostic_metrics(times, events, lp):
    # Use risk score approximation for C-index and time-dependent AUC
    n = len(times)
    # C-index
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
    c_index = concordant / comparable if comparable else None

    # Time-dependent AUC at median time
    t_med = sorted(times)[len(times) // 2]
    y = [1 if events[i] == 1 and times[i] <= t_med else 0 for i in range(n)]
    pos = [lp[i] for i in range(n) if y[i] == 1]
    neg = [lp[i] for i in range(n) if y[i] == 0]
    td_auc = None
    if pos and neg:
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
        td_auc = min(max(U / (len(pos) * len(neg)), 0.0), 1.0)

    # NOTE: Survival Brier score and time-dependent AUC require censoring-aware estimators
    # (e.g., IPCW-based scoring rules). The current placeholder below is intentionally omitted
    # because naive MSE at a fixed time and unweighted binary AUC misrepresent calibration and
    # discrimination in censored data. Report these as unsupported unless proper estimators are
    # implemented and validated.
    brier = None
    td_auc = None

    unsupported_reasons = []
    if td_auc is None:
        unsupported_reasons.append('time_dependent_auc requires censoring-aware estimator')
    if brier is None:
        unsupported_reasons.append('brier requires censoring-aware estimator')
    return {
        'c_index': round(c_index, 4) if c_index is not None else None,
        'time_dependent_auc': td_auc,
        'brier': brier,
        'auc': None,
        'sensitivity': None,
        'specificity': None,
        'unsupported_reasons': unsupported_reasons,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--external-data', required=True)
    ap.add_argument('--threshold', type=float, default=0.5)
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    base_dir = manifest_path.parent
    m = load_json(manifest_path)
    ext_path = Path(args.external_data).resolve()
    if not ext_path.exists():
        print(f"FAIL: external data not found: {ext_path}")
        sys.exit(1)

    study_type = m.get('study_type', '')
    col_map = m.get('column_map', {}) or {}
    id_col = col_map.get('id')
    feature_cols = [c for c in m.get('model_spec', {}).get('features', []) if c]
    model_spec = m.get('model_spec', {}) or {}
    preprocessing = model_spec.get('preprocessing', {}) or {}
    coefs = np.array(model_spec.get('coefficients', []), dtype=float)
    intercept = float(model_spec.get('intercept', 0.0))

    if study_type not in ('diagnostic', 'prognostic'):
        print(f"FAIL: external validation not supported for study_type={study_type}")
        sys.exit(1)

    if coefs.size == 0:
        print("FAIL: model_spec.coefficients empty")
        sys.exit(1)

    if not id_col or not feature_cols:
        print("FAIL: manifest missing id/features")
        sys.exit(1)

    # check ID overlap with existing splits
    split = m.get('split_manifest', {}) or {}
    existing_ids = set()
    for k in ['train', 'validation', 'test']:
        existing_ids.update(split.get(k, []))
    external_ids = []

    if study_type == 'diagnostic':
        outcome_col = col_map.get('outcome')
        if not outcome_col:
            print("FAIL: diagnostic study requires outcome column")
            sys.exit(1)
        ids, X, y = read_diagnostic_data(ext_path, feature_cols, outcome_col, id_col)
        external_ids = ids

        # Reuse dev set mean/std from preprocessing when available
        mean = preprocessing.get('mean')
        std = preprocessing.get('std')
        if preprocessing.get('standardize') and mean and std and len(mean) == len(std) == len(feature_cols):
            X = (X - np.array(mean)) / np.array(std)
        elif preprocessing.get('standardize'):
            print("WARNING: standardize requested but mean/std missing; using raw features.")

        logits = X @ coefs + intercept
        probs = 1.0 / (1.0 + np.exp(-logits))
        metrics = compute_diagnostic_metrics(y.tolist(), probs.tolist(), threshold=args.threshold)

    else:
        time_col = col_map.get('time')
        event_col = col_map.get('event')
        if not time_col or not event_col:
            print("FAIL: prognostic study requires time/event columns")
            sys.exit(1)
        ids, X, times, events = read_prognostic_data(ext_path, feature_cols, time_col, event_col, id_col)
        external_ids = ids

        mean = preprocessing.get('mean')
        std = preprocessing.get('std')
        if preprocessing.get('standardize') and mean and std and len(mean) == len(std) == len(feature_cols):
            X = (X - np.array(mean)) / np.array(std)
        elif preprocessing.get('standardize'):
            print("WARNING: standardize requested but mean/std missing; using raw features.")

        lp = (X @ coefs).tolist()
        metrics = compute_prognostic_metrics(times, events, lp)

    overlap = set(external_ids) & existing_ids
    if overlap:
        print(f"FAIL: external IDs overlap with development splits: {sorted(list(overlap))[:10]}")
        sys.exit(1)

    if len(external_ids) != len(set(external_ids)):
        print("FAIL: duplicate IDs in external data")
        sys.exit(1)

    ext_metrics_path = base_dir / 'external_metrics.json'
    save_json(ext_metrics_path, metrics)

    ext_validation = {
        'status': 'completed',
        'external_data_path': str(ext_path.relative_to(base_dir)) if ext_path.is_relative_to(base_dir) else str(ext_path),
        'external_ids': external_ids,
        'external_metrics': metrics,
    }
    m.setdefault('external_validation', {})
    m['external_validation'].update(ext_validation)
    save_json(manifest_path, m)

    print('wrote', ext_metrics_path)
    print('updated', manifest_path)


if __name__ == '__main__':
    main()
