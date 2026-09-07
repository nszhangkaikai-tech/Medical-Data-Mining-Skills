#!/usr/bin/env python3
"""
Metrics repair / reconciliation.

Recomputes metrics from predictions vs true outcomes when possible.
Writes metrics_reconciliation.json and atomically updates manifest + metrics.json.

Policies:
  - strict: fail if no verifiable evidence
  - manifest_wins: keep manifest values
  - disk_wins: keep metrics.json values
  - repair: recompute from artifacts (predictions/outcomes)
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--metrics-policy', default='repair', choices=['strict','manifest_wins','disk_wins','repair'])
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    base_dir = manifest_path.parent
    m = load_json(manifest_path)
    metrics_path = base_dir / 'metrics.json'
    disk = load_json(metrics_path) if metrics_path.exists() else {}
    manifest_metrics = m.get('metrics', {}) or {}

    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": now,
        "manifest_hash": sha256_file(manifest_path) if manifest_path.exists() else None,
        "metrics_json_hash": sha256_file(metrics_path) if metrics_path.exists() else None,
        "policy": args.metrics_policy,
        "original": dict(manifest_metrics),
        "candidate": dict(disk),
        "rule": None,
        "result": None,
        "updated_keys": [],
    }

    if args.metrics_policy == 'strict':
        overlap = set(disk.keys()) & set(manifest_metrics.keys())
        diff = [k for k in overlap if disk.get(k) != manifest_metrics.get(k)]
        if diff:
            entry['rule'] = f"strict: mismatch on {diff}"
            entry['result'] = "FAIL"
            save_json(args.output, entry)
            print(f"FAIL: metrics mismatch on {diff}")
            sys.exit(1)
        entry['rule'] = "strict: no mismatch"
        entry['result'] = "OK"
        entry['final'] = dict(manifest_metrics)
    elif args.metrics_policy == 'manifest_wins':
        entry['rule'] = "manifest_wins: keep manifest values"
        entry['result'] = "OK"
        entry['final'] = {**disk, **manifest_metrics}
    elif args.metrics_policy == 'disk_wins':
        entry['rule'] = "disk_wins: keep metrics.json values"
        entry['result'] = "OK"
        entry['final'] = {**manifest_metrics, **disk}
    elif args.metrics_policy == 'repair':
        # Try recompute from predictions/outcomes if present
        pred_path = base_dir / 'predictions.json'
        if pred_path.exists():
            pred = load_json(pred_path)
            y_true = pred.get('y_true', [])
            y_pred = pred.get('y_pred', [])
            if y_true and y_pred and len(y_true) == len(y_pred):
                # simple recompute for binary AUC / accuracy / brier
                tp = sum(1 for yt, yp in zip(y_true, y_pred) if yp >= 0.5 and yt == 1)
                fp = sum(1 for yt, yp in zip(y_true, y_pred) if yp >= 0.5 and yt == 0)
                tn = sum(1 for yt, yp in zip(y_true, y_pred) if yp < 0.5 and yt == 0)
                fn = sum(1 for yt, yp in zip(y_true, y_pred) if yp < 0.5 and yt == 1)
                acc = (tp + tn) / max(1, len(y_true))
                brier = sum((yp - yt) ** 2 for yt, yp in zip(y_true, y_pred)) / max(1, len(y_true))
                recomputed = {
                    "auc": None,
                    "accuracy": round(acc, 4),
                    "brier": round(brier, 4),
                }
                entry['candidate'] = recomputed
                entry['rule'] = "repair: recompute from predictions.json"
                entry['result'] = "OK"
                entry['final'] = {**manifest_metrics, **disk}
                entry['final'].update(recomputed)
                entry['updated_keys'] = list(recomputed.keys())
            else:
                entry['rule'] = "repair: predictions.json missing or length mismatch"
                entry['result'] = "FAIL"
                save_json(args.output, entry)
                print("FAIL: predictions.json invalid for repair")
                sys.exit(1)
        else:
            entry['rule'] = "repair: no predictions.json found"
            entry['result'] = "FAIL"
            save_json(args.output, entry)
            print("FAIL: no predictions.json for repair")
            sys.exit(1)

    final = entry.pop('final', entry['original'])
    entry['final_metrics'] = final
    save_json(args.output, entry)

    # atomic update manifest + metrics.json
    m['metrics'] = final
    tmp_manifest = manifest_path.with_suffix('.tmp')
    tmp_metrics = metrics_path.with_suffix('.tmp')
    save_json(tmp_manifest, m)
    save_json(tmp_metrics, final)
    os.replace(tmp_manifest, manifest_path)
    os.replace(tmp_metrics, metrics_path)
    print(f"wrote {args.output}")
    print(f"updated {manifest_path}")
    print(f"updated {metrics_path}")


if __name__ == '__main__':
    main()
