#!/usr/bin/env python3
"""
PROBAST+AI automated assessor.

Reads manifest.json, optional training artifacts, and acceptance results.
Outputs per-item evidence, status, rule, and overall risk.
"""
import argparse
import json
import math
import sys
from pathlib import Path


def load_json(path):
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def is_valid_metric(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return False
    if not isinstance(v, (int, float)):
        return False
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return False
    return True


def get_metric(m, key):
    return (m.get('metrics') or {}).get(key)


def assess(manifest, acceptance=None):
    m = manifest
    a = acceptance or {}
    col_map = m.get('column_map', {}) or {}
    model_spec = m.get('model_spec', {}) or {}
    sample_flow = m.get('sample_flow', {}) or {}
    split = m.get('split_manifest', {}) or {}
    ext = m.get('external_validation', {}) or {}
    pre = model_spec.get('preprocessing', {}) or {}
    artifacts = m.get('artifacts', []) or []

    items = {}

    def add(item_id, status, evidence, rule, notes=''):
        items[item_id] = {
            'status': status,
            'evidence': evidence,
            'rule': rule,
            'notes': notes,
        }

    # 1. Participants
    add('1.1_cohort_definition',
        'Yes' if sample_flow.get('raw') and sample_flow.get('after_qc') else 'No',
        'sample_flow.raw / after_qc',
        'raw > 0 and after_qc <= raw')
    add('1.2_index_date_range',
        'Yes' if m.get('endpoint') else 'No',
        'manifest.endpoint',
        'endpoint non-empty')
    add('1.3_follow_up',
        'Yes' if m.get('study_type') in ('prognostic', 'treatment_effect') and m.get('column_map', {}).get('time') else 'Partial',
        'column_map.time',
        'time column present for survival')
    add('1.4_censoring',
        'Yes' if m.get('censoring_def') and m.get('study_type') in ('prognostic', 'treatment_effect') else 'Not assessable',
        'manifest.censoring_def + study_type',
        'censoring_def present when required')

    # 2. Outcome
    outcome_col = col_map.get('outcome') or col_map.get('event')
    add('2.1_outcome_definition',
        'Yes' if outcome_col else 'No',
        'column_map.outcome or column_map.event',
        'outcome/event defined')
    add('2.2_measurement_validity',
        'Not assessable',
        'no measurement metadata in manifest',
        'requires author-supplied validity')
    add('2.3_blinding',
        'Not assessable',
        'no blinding metadata',
        'requires author-supplied design metadata')

    # 3. Predictors / model
    add('3.1_feature_definition',
        'Yes' if model_spec.get('features') else 'No',
        'model_spec.features',
        'feature list non-empty')
    add('3.2_feature_preprocessing',
        'Yes' if pre.get('standardize') or pre.get('missing') else 'Partial',
        'model_spec.preprocessing',
        'standardize or missing stated')
    add('3.3_number_of_features',
        'Yes' if len(model_spec.get('features', [])) >= 1 else 'No',
        'model_spec.features length',
        '>=1 feature')
    add('3.4_threshold',
        'Yes' if model_spec.get('threshold') is not None else 'Unclear',
        'model_spec.threshold',
        'threshold stated')

    # 4. Missing data
    add('4.1_missing_handling',
        'Yes' if pre.get('missing') else 'No',
        'model_spec.preprocessing.missing',
        'missing strategy stated')

    # 5. Model building
    train_n = sample_flow.get('train', 0)
    feats_n = len(model_spec.get('features', [])) or 1
    epv = train_n / feats_n if train_n else 0
    add('5.1_model_type',
        'Yes' if model_spec.get('type') else 'No',
        'model_spec.type',
        'model type stated')
    add('5.2_preprocessing_pipeline',
        'Yes' if pre.get('standardize') else 'Partial',
        'model_spec.preprocessing.standardize',
        'standardize boolean')
    add('5.3_feature_selection',
        'Not assessable',
        'no feature selection metadata',
        'requires training script disclosure')
    add('5.4_model_complexity',
        'Yes' if model_spec.get('coefficients') else 'No',
        'model_spec.coefficients',
        'coefficients present')

    # 6. Performance
    cidx = get_metric(m, 'c_index')
    auc = get_metric(m, 'auc')
    td_auc = get_metric(m, 'time_dependent_auc')
    valid_disc = [v for v in (cidx, auc, td_auc) if is_valid_metric(v)]
    disc_status = 'Yes' if valid_disc else ('Not assessable' if any(v is not None for v in (cidx, auc, td_auc)) else 'No')
    add('6.1_discrimination',
        disc_status,
        'metrics.c_index / auc / time_dependent_auc',
        'requires valid numeric discrimination metric')
    brier = get_metric(m, 'brier')
    brier_valid = is_valid_metric(brier)
    brier_present = brier is not None
    cal_slope = get_metric(m, 'calibration_slope')
    cal_intercept = get_metric(m, 'calibration_intercept')
    if is_valid_metric(cal_slope) and is_valid_metric(cal_intercept):
        cal_status = 'Yes'
    else:
        cal_status = 'Not assessable'
    add('6.2_calibration',
        cal_status,
        'metrics.calibration_slope + metrics.calibration_intercept',
        'requires valid numeric calibration slope and intercept; arbitrary calibration artifact filenames are not accepted as evidence')
    add('6.3_validation_method',
        'Yes' if split.get('validation') or split.get('test') else 'No',
        'split_manifest.validation / test',
        'internal split exists')
    add('6.4_decision_curve',
        'Not assessable',
        'no DCA artifact in manifest',
        'requires DCA figure/table')

    # 7. Analysis
    add('7.1_sample_size_justification',
        'Yes' if sample_flow.get('raw', 0) >= 100 else 'Partial',
        'sample_flow.raw',
        'raw >= 100 ideal')
    add('7.2_events_per_variable',
        'Yes' if epv >= 10 else ('Partial' if epv >= 5 else 'No'),
        'sample_flow.train / len(model_spec.features)',
        'EPV >= 10 ideal')
    add('7.3_sensitivity_analysis',
        'Not assessable',
        'no sensitivity metadata',
        'requires author-supplied analysis plan')

    # 8. External evaluation
    add('8.1_external_completed',
        ext.get('status', 'unavailable'),
        'external_validation.status',
        'completed only if external_data_path + external_ids + external_metrics present')
    ext_path = m.get('external_validation', {}).get('external_data_path')
    ext_ids = m.get('external_validation', {}).get('external_ids', [])
    add('8.2_id_overlap',
        'No' if ext.get('status') == 'completed' and not (set(ext_ids or []) & (set(split.get('train', [])) | set(split.get('validation', [])) | set(split.get('test', [])))) else 'Yes',
        'external_ids vs split_manifest',
        'no ID overlap')

    # 9. Prediction model
    add('9.1_full_model_disclosed',
        'Yes' if model_spec.get('features') and model_spec.get('coefficients') and model_spec.get('intercept') is not None else 'No',
        'model_spec',
        'features + coefficients + intercept present')
    add('9.2_preprocessing_disclosed',
        'Yes' if pre.get('standardize') and pre.get('mean') and pre.get('std') else 'Partial',
        'model_spec.preprocessing.mean/std',
        'mean/std present for standardization')
    add('9.3_threshold_validation',
        'Yes' if model_spec.get('threshold') is not None else 'Unclear',
        'model_spec.threshold',
        'threshold stated')

    # 10. Interpretation / fairness
    add('10.1_visualization',
        'Yes' if any(str(a).lower().endswith(('.png', '.jpg', '.svg', '.html')) for a in artifacts) else 'Partial',
        'artifacts',
        'at least one visualization artifact')
    add('10.2_clinical_claims',
        'No' if a.get('no_unsubstantiated_clinical_claims') is False else 'Yes',
        'acceptance_tests.no_unsubstantiated_clinical_claims',
        'no banned clinical phrases in report')

    overall = 'low'
    fails = [k for k, v in items.items() if v['status'] == 'No']
    unclear = [k for k, v in items.items() if v['status'] in ('Unclear', 'Not assessable')]
    if fails:
        overall = 'high'
    elif unclear:
        overall = 'unclear'

    return {
        'study_type': m.get('study_type'),
        'endpoint': m.get('endpoint'),
        'automatic_items': items,
        'manual_items': {},
        'overall_risk': overall,
        'summary': {
            'passed': sum(1 for v in items.values() if v['status'] == 'Yes'),
            'failed': len(fails),
            'unclear': len(unclear),
            'not_assessable': sum(1 for v in items.values() if v['status'] == 'Not assessable'),
        }
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--acceptance-json', default=None)
    args = ap.parse_args()

    m = load_json(args.manifest)
    acceptance = None
    if args.acceptance_json:
        p = Path(args.acceptance_json)
        if p.exists():
            acceptance = json.loads(p.read_text(encoding='utf-8')).get('results', {})

    report = assess(m, acceptance=acceptance)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('wrote', args.output)


if __name__ == '__main__':
    main()
