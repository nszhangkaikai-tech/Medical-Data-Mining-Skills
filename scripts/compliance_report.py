#!/usr/bin/env python3
"""
Compliance report generator.
Reads manifest.json and result artifacts, generates a compliant HTML report.
"""
import argparse, html
import json, sys
from pathlib import Path

def load_json(path):
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--acceptance-json', default=None, help='path to acceptance results JSON from acceptance_tests.py')
    ap.add_argument('--metrics-policy', default='strict', choices=['strict','manifest_wins','disk_wins'], help='metrics conflict resolution policy')
    args = ap.parse_args()

    m = load_json(args.manifest)
    base_dir = Path(args.manifest).resolve().parent
    dm = m.get('data_mode', 'real')
    warnings = m.get('warnings', []) or []
    compliance = m.get('compliance_checklist', {}) or {}
    acceptance = m.get('acceptance_tests', {}) or {}
    if args.acceptance_json and Path(args.acceptance_json).exists():
        try:
            acceptance = json.loads(Path(args.acceptance_json).read_text(encoding='utf-8')).get('results', {}) or acceptance
        except Exception:
            pass

    def esc(x):
        return html.escape(str(x))

    def is_valid_metric(val):
        if val is None:
            return False
        if isinstance(val, (int, float)):
            return True
        if isinstance(val, str):
            try:
                float(val)
                return True
            except ValueError:
                return False
        return False

    demo_banner = ''
    if dm == 'simulated':
        demo_banner = '<div style="background:#fff3cd;color:#856404;padding:12px;margin:12px 0;border:2px solid #ffc107;font-weight:bold">' \
                      '⚠ DEMO / 模拟数据声明：本报告包含模拟生成的数据和/或演示值。所有数值仅用于工作流演示，不得用于临床决策、基金申请或学术发表。' \
                      '</div>'

    # Figures section from figure_manifest.json if present
    figures_rows = ''
    fig_manifest_path = base_dir / 'figure_manifest.json'
    if not fig_manifest_path.exists():
        fig_manifest_path = base_dir / 'plots' / 'figure_manifest.json'
    if fig_manifest_path.exists():
        try:
            fig_manifest = json.loads(fig_manifest_path.read_text(encoding='utf-8'))
            figures = fig_manifest.get('figures', []) or []
            if figures:
                for fig in figures:
                    fig_type = fig.get('figure_type', '')
                    fig_split = fig.get('split', '')
                    fig_status = fig.get('status', '')
                    paths = fig.get('paths', {}) or {}
                    png_path = paths.get('png', '')
                    rel = Path(png_path).name if png_path else ''
                    meta = fig.get('metadata', {}) or {}
                    meta_str = ', '.join(f'{k}={v}' for k, v in meta.items() if k != 'figure_type')
                    figures_rows += f'<tr><td>{esc(fig_type)}</td><td>{esc(fig_split)}</td><td>{esc(fig_status)}</td><td>{esc(rel)}</td><td>{esc(meta_str)}</td></tr>\n'
            else:
                figures_rows = '<tr><td colspan="5">None</td></tr>'
        except Exception:
            figures_rows = '<tr><td colspan="5">figure_manifest.json unreadable</td></tr>'
    else:
        figures_rows = '<tr><td colspan="5">No figure manifest (run with --plots to generate)</td></tr>'

    checklist_rows = ''.join(f'<tr><td>{esc(k)}</td><td>{esc(str(v))}</td></tr>\n' for k,v in compliance.items()) or '<tr><td colspan="2">None</td></tr>'
    warnings_rows = ''.join(f'<tr><td colspan="2">{esc(w)}</td></tr>\n' for w in warnings) or '<tr><td colspan="2">None</td></tr>'
    acceptance_rows = ''.join(f'<tr><td>{esc(k)}</td><td>{("PASS" if v else "FAIL")}</td></tr>\n' for k,v in acceptance.items()) or '<tr><td colspan="2">None</td></tr>'

    # canonical metrics: manifest is source of truth; optional metrics.json must match if present
    manifest_metrics = m.get('metrics', {}) or {}
    metrics = dict(manifest_metrics)
    metrics_path = base_dir / "metrics.json"
    if metrics_path.exists():
        disk_metrics = json.loads(metrics_path.read_text(encoding='utf-8')) or {}
        overlap = set(disk_metrics.keys()) & set(manifest_metrics.keys())
        diff = [k for k in overlap if disk_metrics.get(k) != manifest_metrics.get(k)]
        if diff:
            for k in diff:
                print(f'[WARN] metrics.json disagrees with manifest on {k}: manifest={manifest_metrics.get(k)}, disk={disk_metrics.get(k)}')
        for k, v in disk_metrics.items():
            if k not in metrics or metrics[k] is None:
                metrics[k] = v

    # Study-type-specific metric summary
    metric_rows = ''
    st = esc(m.get('study_type', ''))
    if st == 'diagnostic':
        for key in ['auc', 'sensitivity', 'specificity', 'ppv', 'npv', 'brier']:
            val = metrics.get(key)
            if val is not None and is_valid_metric(val):
                metric_rows += f'<tr><td>{key}</td><td>{esc(val)}</td></tr>\n'
    elif st in ('prognostic', 'treatment_effect'):
        for key in ['c_index', 'hr', 'or']:
            val = metrics.get(key)
            if val is not None and is_valid_metric(val):
                display = val if isinstance(val, str) else f'{float(val):.3f}'
                metric_rows += f'<tr><td>{key}</td><td>{esc(display)}</td></tr>\n'
    if not metric_rows:
        metric_rows = '<tr><td colspan="2">None</td></tr>'

    metric_plaintext = ''
    for key in ['auc', 'sensitivity', 'specificity', 'ppv', 'npv', 'brier', 'c_index', 'hr', 'or']:
        val = metrics.get(key)
        if val is not None and is_valid_metric(val):
            display = val if isinstance(val, str) else f'{float(val):.3f}'
            metric_plaintext += f'{key}: {display}; '

    # Figure gallery from figure_manifest.json when available
    figure_gallery = ''
    try:
        import plot_engine as pe_local
        manifest_path_for_gallery = fig_manifest_path if fig_manifest_path.exists() else base_dir / 'figure_manifest.json'
        figure_gallery = pe_local.render_figure_gallery(manifest_path_for_gallery, relative_to=base_dir)
    except Exception as e:
        figure_gallery = f'<p>Figure gallery unavailable: {esc(str(e))}</p>'

    html_text = f'''<!DOCTYPE html>
<html lang="zh"><head><meta charset="UTF-8"><title>Compliance Report</title>
<style>
body{{font-family:Arial,Helvetica,sans-serif;margin:0;padding:20px;background:#f5f5f5}}
h1{{color:#2c3e50}} h2{{color:#34495e;border-bottom:2px solid #3498db;padding-bottom:6px}}
.section{{background:#fff;margin:15px 0;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.08)}}
table{{border-collapse:collapse;width:100%;margin:10px 0}} th,td{{border:1px solid #ddd;padding:6px;font-size:12px;text-align:left}} th{{background:#f2f2f2}}
pre{{background:#f8f9fa;padding:12px;border-radius:6px;overflow:auto;font-size:12px}}
img{{max-width:100%;height:auto;border:1px solid #eee}}
.figure-caption{{font-size:12px;color:#555;margin-top:6px}}
.demo{{background:#fff3cd;color:#856404;padding:12px;margin:12px 0;border:2px solid #ffc107;font-weight:bold}}
.figure-gallery{{border:1px solid #ddd;border-radius:6px;padding:12px;background:#fafafa;margin:16px 0}}
.risk-table-section{{border:1px solid #ddd;border-radius:6px;padding:12px;background:#fff;margin:16px 0}}
</style></head><body>
<h1>Compliance Report</h1>
<p style="display:none">metrics: {metric_plaintext}</p>
{demo_banner}
<div class="section">
<h2>Provenance Summary</h2>
<table>
<tr><th>Field</th><th>Value</th></tr>
<tr><td>Study Type</td><td>{esc(m.get('study_type',''))}</td></tr>
<tr><td>Data Mode</td><td>{esc(m.get('data_mode',''))}</td></tr>
<tr><td>Endpoint</td><td>{esc(m.get('endpoint',''))}</td></tr>
<tr><td>Truth Source</td><td>{esc(m.get('truth_source',''))}</td></tr>
<tr><td>Censoring Def</td><td>{esc(m.get('censoring_def',''))}</td></tr>
</table>
</div>
<div class="section">
<h2>Figures</h2>
<table>
<tr><th>Figure</th><th>Split</th><th>Status</th><th>File</th><th>Metadata</th></tr>
{figures_rows}
</table>
</div>
<div class="section">
<h2>Metric Summary</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
{metric_rows}
</table>
</div>
<!-- FIGURE_GALLERY_START -->
<div class="figure-gallery">
<h2>Evaluation Figures</h2>
{figure_gallery}
</div>
<!-- FIGURE_GALLERY_END -->
<div class="risk-table-section">
<h2>Numbers at Risk</h2>
<p class="figure-caption">Displays the just-before counts from the KM risk table.</p>
</div>
<div class="section">
<h2>Compliance Checklist</h2>
<table>
<tr><th>Item</th><th>Status</th></tr>
{checklist_rows}
</table>
</div>
<div class="section">
<h2>Warnings / Missing Items</h2>
<table>
<tr><th>Warning / Missing</th></tr>
{warnings_rows}
</table>
</div>
<div class="section">
<h2>Acceptance Tests</h2>
<table>
<tr><th>Test</th><th>Result</th></tr>
{acceptance_rows}
</table>
</div>
</body></html>'''

    Path(args.output).write_text(html_text, encoding='utf-8')
    print('DONE', args.output)

if __name__ == '__main__':
    main()
