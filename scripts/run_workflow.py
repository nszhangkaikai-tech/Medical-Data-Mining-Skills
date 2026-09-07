#!/usr/bin/env python3
"""
Real data workflow orchestrator for medical-data-mining skill.

Manifest-driven:
  - validates manifest
  - routes training by study_type (diagnostic / prognostic)
  - optional external validation, PROBAST+AI, metrics repair
  - runs acceptance tests
  - generates compliance report
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_FIELDS = [
    'study_type','data_mode','endpoint','truth_source',
    'input_files','column_map','split_manifest','model_spec',
    'metrics','sample_flow','artifacts'
]

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import plot_engine as pe


def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))


def resolve_artifact(path_str, base_dir):
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def validate_manifest(manifest, base_dir):
    missing = [k for k in REQUIRED_FIELDS if k not in manifest or manifest[k] is None]
    if missing:
        raise ValueError(f"manifest missing required fields: {missing}")

    sf = manifest.get('sample_flow', {}) or {}
    if sf.get('raw', 0) <= 0:
        raise ValueError("sample_flow.raw must be > 0")
    if sf.get('after_qc', 0) <= 0:
        raise ValueError("sample_flow.after_qc must be > 0")
    if sf.get('after_qc', 0) > sf.get('raw', 0):
        raise ValueError("sample_flow.after_qc cannot exceed raw")
    split_total = sum(sf.get(k, 0) for k in ['train','validation','test','external'])
    if split_total > sf.get('after_qc', 0):
        raise ValueError(f"split total {split_total} exceeds after_qc {sf.get('after_qc', 0)}")

    artifacts = manifest.get('artifacts', []) or []
    missing_artifacts = [a for a in artifacts if resolve_artifact(a, base_dir).exists() is False]
    if missing_artifacts:
        print(f"[WARN] artifacts not yet generated (will be checked after training): {missing_artifacts}")

    feats = (manifest.get('model_spec', {}) or {}).get('features', [])
    coefs = (manifest.get('model_spec', {}) or {}).get('coefficients', [])
    if feats and coefs and len(feats) != len(coefs):
        raise ValueError("model_spec.coefficients length must equal features length")


def run_script(name, args_list):
    script = SCRIPT_DIR / name
    if not script.exists():
        return None
    return subprocess.run(
        [sys.executable, str(script)] + args_list,
        capture_output=True, text=True
    )


def main():
    ap = argparse.ArgumentParser(description="Run real-data workflow from manifest")
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--metrics-policy', default='strict', choices=['strict','manifest_wins','disk_wins','repair'])
    ap.add_argument('--allow-network', action='store_true', help='allow real API calls for enrichment/PPI')
    ap.add_argument('--train', action='store_true', help='run trainer for study_type')
    ap.add_argument('--plots', action='store_true', help='generate evaluation plots (ROC/PR/calibration/KM) into a figures/ subdir')
    ap.add_argument('--external-validation', action='store_true', help='run external validation if manifest requests it')
    ap.add_argument('--probast', action='store_true', help='run PROBAST+AI assessor')
    ap.add_argument('--enrichment', action='store_true', help='run enrichment analysis')
    ap.add_argument('--ppi', action='store_true', help='run PPI analysis')
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        print(f"manifest not found: {manifest_path}")
        sys.exit(1)

    manifest = load_json(manifest_path)
    if manifest is None:
        print("manifest is not valid JSON")
        sys.exit(1)

    base_dir = manifest_path.resolve().parent

    print("=" * 60)
    print("Medical Data Mining Skill - Workflow Orchestrator")
    print("=" * 60)
    print(f"manifest: {manifest_path}")

    try:
        validate_manifest(manifest, base_dir)
        print("[OK] manifest validation passed")
    except ValueError as e:
        print(f"[FAIL] manifest validation: {e}")
        sys.exit(1)

    acceptance_json = base_dir / "acceptance_results.json"
    report_path = base_dir / "compliance_report.html"

    # 1. optional training
    if args.train:
        study_type = manifest.get('study_type')
        if study_type == 'diagnostic':
            trainer = SCRIPT_DIR / 'trainers' / 'diagnostic_logistic.py'
        elif study_type == 'prognostic':
            trainer = SCRIPT_DIR / 'trainers' / 'prognostic_cox.py'
        else:
            print(f"[SKIP] training not implemented for study_type={study_type}")
            trainer = None
        if trainer and trainer.exists():
            print(f"\n[STEP] running trainer: {trainer.name}")
            res = run_script(str(trainer.relative_to(SCRIPT_DIR)), ['--manifest', str(manifest_path)])
            if res and res.returncode != 0:
                print(res.stdout)
                print(res.stderr)
                print("[FAIL] trainer failed")
                sys.exit(1)
            print(res.stdout if res else "")
            print("[OK] trainer completed")
            manifest = load_json(manifest_path)

    # 1c. optional evaluation plots
    figures_manifest_path = None
    if args.plots:
        print("\n[STEP] generating evaluation plots")
        figures_dir = base_dir / "plots"
        figures_dir.mkdir(parents=True, exist_ok=True)
        study_type = manifest.get('study_type')
        data_mode = manifest.get('data_mode', 'real')
        figures: List[Dict[str, Any]] = []
        pred_path = base_dir / 'predictions.json'
        train_pred_path = base_dir / 'predictions_train.json'
        pred = load_json(pred_path)
        if not pred:
            print("[WARN] predictions.json not found; skipping plots")
            figures.append({
                "figure_type": "placeholder",
                "status": "not_generated",
                "reason": "predictions.json not found",
                "split": split,
                "data_mode": data_mode,
                "paths": {},
                "metadata": {},
            })
        else:
            source_hash = pred.get('data_hash', '') or ''
            split = pred.get('split', 'validation')
            if study_type == 'diagnostic':
                y_true = pred.get('y_true', [])
                y_prob = pred.get('y_prob', [])
                if y_true and y_prob:
                    out = pe.plot_roc(y_true, y_prob, output_dir=figures_dir, source_hash=source_hash, split=split, data_mode=data_mode)
                    figures.append(out)
                    out = pe.plot_pr(y_true, y_prob, output_dir=figures_dir, source_hash=source_hash, split=split, data_mode=data_mode)
                    figures.append(out)
                    out = pe.plot_calibration(y_true, y_prob, output_dir=figures_dir, source_hash=source_hash, split=split, data_mode=data_mode)
                    figures.append(out)
                else:
                    for name in ("roc_curve", "pr_curve", "calibration_curve"):
                        figures.append({
                            "figure_type": name,
                            "status": "not_generated",
                            "reason": "missing y_true or y_prob in predictions.json",
                            "split": split,
                            "data_mode": data_mode,
                            "paths": {},
                            "metadata": {},
                        })
                train_pred = load_json(train_pred_path)
                if train_pred and train_pred.get('y_true') and train_pred.get('y_prob'):
                    out = pe.plot_roc(train_pred['y_true'], train_pred['y_prob'], output_dir=figures_dir, filename='roc_curve_train.png', source_hash=source_hash, split='train', data_mode=data_mode)
                    figures.append(out)
            elif study_type == 'prognostic':
                times = pred.get('time', [])
                events = pred.get('event', [])
                groups = pred.get('risk_group', [])
                if times and events and groups:
                    out = pe.plot_km(times, events, groups, output_dir=figures_dir, source_hash=source_hash, split=split, data_mode=data_mode)
                    figures.append(out)
                else:
                    figures.append({
                        "figure_type": "km_curve",
                        "status": "not_generated",
                        "reason": "missing time/event/risk_group in predictions.json",
                        "split": split,
                        "data_mode": data_mode,
                        "paths": {},
                        "metadata": {},
                    })
                train_pred = load_json(train_pred_path)
                if train_pred and train_pred.get('time') and train_pred.get('event') and train_pred.get('risk_group'):
                    out = pe.plot_km(train_pred['time'], train_pred['event'], train_pred['risk_group'], output_dir=figures_dir, filename='km_curve_train.png', source_hash=source_hash, split='train', data_mode=data_mode)
                    figures.append(out)
        if figures:
            figures_manifest_path = pe.write_figure_manifest(figures, figures_dir)
            print(f"[OK] generated {len([f for f in figures if f.get('status')=='generated'])}/{len(figures)} figures -> {figures_dir}")
            print(f"[OK] figure manifest -> {figures_manifest_path}")

            gallery_html = pe.render_figure_gallery(figures_manifest_path, relative_to=base_dir)
            gallery_block = (
                '<!-- FIGURE_GALLERY_START -->\n'
                '<div class="figure-gallery">\n'
                f'  <h2>Evaluation Figures</h2>\n'
                f'  {gallery_html}\n'
                '</div>\n'
                '<!-- FIGURE_GALLERY_END -->'
            )
            report_path = base_dir / 'report.html'
            if report_path.exists():
                html_text = report_path.read_text(encoding='utf-8')
                start_marker = '<!-- FIGURE_GALLERY_START -->'
                end_marker = '<!-- FIGURE_GALLERY_END -->'
                start_idx = html_text.find(start_marker)
                end_idx = html_text.find(end_marker)
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    html_text = html_text[:start_idx] + gallery_block + html_text[end_idx + len(end_marker):]
                else:
                    html_text = html_text + '\n' + gallery_block
                report_path.write_text(html_text, encoding='utf-8')
                print('[OK] patched report.html figure gallery')
        else:
            print("[WARN] no figures generated")

    # 1b. metrics reconciliation (repair)
    if args.metrics_policy == 'repair':
        print("\n[STEP] metrics repair")
        repair_script = SCRIPT_DIR / 'metrics_repair.py'
        if repair_script.exists():
            repair_json = base_dir / 'metrics_reconciliation.json'
            res = run_script(str(repair_script.relative_to(SCRIPT_DIR)), [
                '--manifest', str(manifest_path),
                '--output', str(repair_json)
            ])
            if res and res.returncode != 0:
                print(res.stdout)
                print(res.stderr)
                print("[FAIL] metrics repair failed")
                sys.exit(1)
            print(res.stdout if res else "")
            print("[OK] metrics repair completed")
            manifest = load_json(manifest_path)
        else:
            print("[SKIP] metrics_repair.py not found")

    # 2. external validation
    ext = manifest.get('external_validation', {}) or {}
    if args.external_validation:
        print("\n[STEP] external validation requested")
        ext_status = ext.get('status', 'unavailable')
        ext_path = resolve_artifact(ext.get('external_data_path', ''), base_dir)
        if ext_status != 'pending':
            print(f"[FAIL] external validation status is '{ext_status}', expected 'pending'")
            sys.exit(1)
        if not ext_path or not ext_path.exists():
            print(f"[FAIL] external data missing for requested external validation: {ext.get('external_data_path', '')}")
            sys.exit(1)
        print(f"[STEP] running external validation on {ext_path}")
        res = run_script('external_validation.py', [
            '--manifest', str(manifest_path),
            '--external-data', str(ext_path)
        ])
        if res and res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            print("[FAIL] external validation failed")
            sys.exit(1)
        print(res.stdout if res else "")
        print("[OK] external validation completed")
        manifest = load_json(manifest_path)

    # 3. PROBAST+AI
    if args.probast:
        print("\n[STEP] running PROBAST+AI assessment")
        probast_out = base_dir / 'probast_ai.json'
        res = run_script('probast_ai.py', [
            '--manifest', str(manifest_path),
            '--output', str(probast_out)
        ])
        if res and res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            print("[FAIL] PROBAST+AI failed")
            sys.exit(1)
        print(res.stdout if res else "")
        print("[OK] PROBAST+AI completed")
        manifest = load_json(manifest_path)

    # 4. enrichment / PPI (pass --allow-network through when requested)
    extra_network = ['--allow-network'] if args.allow_network else []
    if args.enrichment:
        print("\n[STEP] running enrichment analysis")
        enrichment_out = base_dir / 'enrichment.json'
        res = run_script('enrichment.py', [
            '--genes', str(manifest.get('enrichment_genes', '')),
            '--output', str(enrichment_out),
        ] + extra_network)
        if res and res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            print("[FAIL] enrichment failed")
            sys.exit(1)
        print(res.stdout if res else "")
        print("[OK] enrichment completed")

    if args.ppi:
        print("\n[STEP] running PPI analysis")
        ppi_out = base_dir / 'ppi.json'
        res = run_script('ppi.py', [
            '--genes', str(manifest.get('ppi_genes', '')),
            '--output', str(ppi_out),
        ] + extra_network)
        if res and res.returncode != 0:
            print(res.stdout)
            print(res.stderr)
            print("[FAIL] PPI failed")
            sys.exit(1)
        print(res.stdout if res else "")
        print("[OK] PPI completed")

    # 5. compliance report
    print("\n[STEP] generating compliance report...")
    compliance_script = SCRIPT_DIR / "compliance_report.py"
    res = subprocess.run(
        [sys.executable, str(compliance_script),
         '--manifest', str(manifest_path),
         '--output', str(report_path),
         '--acceptance-json', str(acceptance_json),
         '--metrics-policy', args.metrics_policy],
        capture_output=True, text=True
    )
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        print("[FAIL] compliance report generation failed")
        sys.exit(1)

    # 6. acceptance tests
    print("\n[STEP] running acceptance tests...")
    acceptance_script = SCRIPT_DIR / "acceptance_tests.py"
    res = subprocess.run(
        [sys.executable, str(acceptance_script), '--manifest', str(manifest_path), '--json', str(acceptance_json), '--metrics-policy', args.metrics_policy],
        capture_output=True, text=True
    )
    print(res.stdout)
    if res.returncode != 0:
        print(res.stderr)
        print("[FAIL] acceptance tests failed")
        sys.exit(1)

    print("\n[DONE] workflow completed successfully")
    print(f"manifest: {manifest_path}")
    print(f"report:   {report_path}")


if __name__ == "__main__":
    main()
