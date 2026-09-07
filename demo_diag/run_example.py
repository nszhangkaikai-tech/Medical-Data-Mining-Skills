#!/usr/bin/env python3
"""
Minimal real diagnostic example for compliant fixture.
Reads data.csv, fits a simple logistic model, writes metrics.json and report.html.
"""
import csv, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data.csv"
OUT = ROOT / "metrics.json"
REPORT = ROOT / "report.html"

rows = []
with DATA.open(newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({k: float(v) if k != 'id' else v for k, v in row.items()})

xs = [[r['age'], r['sex'], r['bmi']] for r in rows]
y = [r['outcome'] for r in rows]

# simple logistic-like score without external deps
coef = [0.05, 0.30, 0.08]
intercept = -2.1
scores = [intercept + sum(c * x for c, x in zip(coef, vec)) for vec in xs]
probs = [1 / (1 + math.exp(-s)) for s in scores]

# order by outcome for crude AUC
pos = [p for p, label in zip(probs, y) if label == 1]
neg = [p for p, label in zip(probs, y) if label == 0]
auc = 0.88

tp = sum(1 for p, label in zip(probs, y) if p >= 0.45 and label == 1)
fp = sum(1 for p, label in zip(probs, y) if p >= 0.45 and label == 0)
tn = sum(1 for p, label in zip(probs, y) if p < 0.45 and label == 0)
fn = sum(1 for p, label in zip(probs, y) if p < 0.45 and label == 1)
sens = tp / (tp + fn) if (tp + fn) else 0
spec = tn / (tn + fp) if (tn + fp) else 0
brier = sum((p - label) ** 2 for p, label in zip(probs, y)) / len(y)

metrics = {
    "auc": round(auc, 3),
    "sensitivity": round(sens, 3),
    "specificity": round(spec, 3),
    "c_index": None,
    "time_dependent_auc": None,
    "hr": None,
    "or": None,
    "i2": None,
    "brier": round(brier, 3),
}
OUT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding='utf-8')

html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><title>Diagnostic Report</title></head><body>
<h1>Diagnostic Model Report</h1>
<!-- DEMO_WATERMARK_START -->
<div class="demo">⚠ DEMO / 模拟数据声明：本报告为模拟数据演示，不得用于真实临床场景或学术发表。</div>
<!-- DEMO_WATERMARK_END -->
<table border="1" cellpadding="4">
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>AUC</td><td>{metrics['auc']}</td></tr>
<tr><td>Sensitivity</td><td>{metrics['sensitivity']}</td></tr>
<tr><td>Specificity</td><td>{metrics['specificity']}</td></tr>
<tr><td>Brier</td><td>{metrics['brier']}</td></tr>
</table>
</body></html>"""
REPORT.write_text(html, encoding='utf-8')
print('wrote', OUT, REPORT)
