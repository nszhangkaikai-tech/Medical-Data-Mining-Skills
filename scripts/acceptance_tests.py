#!/usr/bin/env python3
"""
Real acceptance tests for medical-data-mining skill.
Every check is computed from manifest / raw data / artifacts. No default True booleans.
"""
import argparse, csv, hashlib, json, math, re, sys
from pathlib import Path

def load_json(path):
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding='utf-8'))

def check(name, condition, msg):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}: {msg}")
    return condition

def is_valid_metric(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return False
    if not isinstance(v, (int, float)):
        return False
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return False
    return True

def resolve_path(base_dir, value):
    if value is None:
        return None
    p = Path(str(value))
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def csv_row_col_count(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = 0
        cols = 0
        header_seen = False
        for row in reader:
            if not header_seen:
                header_seen = True
                cols = len(row)
                continue
            rows += 1
            if len(row) != cols:
                cols = max(cols, len(row))
    return rows, cols

def run(manifest_path, metrics_policy='strict'):
    m = load_json(manifest_path)
    if not m:
        print("FAIL: manifest.json not found")
        sys.exit(1)

    base_dir = Path(manifest_path).resolve().parent
    results = {}
    warnings = []

    # canonical metrics: manifest is source of truth; optional metrics.json must match if present
    manifest_metrics = m.get('metrics', {}) or {}
    metrics = dict(manifest_metrics)
    metrics_path = base_dir / "metrics.json"
    if metrics_path.exists():
        disk_metrics = json.loads(metrics_path.read_text(encoding='utf-8')) or {}
        overlap = set(disk_metrics.keys()) & set(manifest_metrics.keys())
        diff = [k for k in overlap if disk_metrics.get(k) != manifest_metrics.get(k)]
        if diff:
            if metrics_policy == 'strict':
                print(f"FAIL: metrics.json disagrees with manifest on keys: {diff}")
                sys.exit(1)
            elif metrics_policy == 'manifest_wins':
                warnings.append(f"metrics conflict on {diff}: manifest wins")
            elif metrics_policy == 'disk_wins':
                warnings.append(f"metrics conflict on {diff}: disk wins")
                for k in diff:
                    metrics[k] = disk_metrics.get(k)
        for k, v in disk_metrics.items():
            if k not in metrics or metrics[k] is None:
                metrics[k] = v

    # 1. required fields + empty string/list checks
    required_present = ['study_type','data_mode','endpoint','truth_source','input_files','column_map','split_manifest','model_spec','metrics','sample_flow','artifacts']
    missing = [k for k in required_present if k not in m or m[k] is None]
    empty_str = [k for k in ['study_type','data_mode','endpoint','truth_source'] if isinstance(m.get(k), str) and not m.get(k).strip()]
    if m.get('study_type') in ('prognostic','treatment_effect'):
        if m.get('censoring_def') is None or (isinstance(m.get('censoring_def'), str) and not m.get('censoring_def').strip()):
            empty_str.append('censoring_def')
    if not (m.get('input_files') or []):
        missing.append('input_files empty')
    if not (m.get('artifacts') or []):
        missing.append('artifacts empty')
    col_map = m.get('column_map', {}) or {}
    if not col_map.get('id'):
        missing.append('column_map.id')
    req_fail = len(missing) > 0 or len(empty_str) > 0
    results['required_fields'] = check('required_fields', not req_fail, f"missing: {missing}; empty: {empty_str}")

    # 1b. input file hash/row/col integrity
    input_ok = True
    input_msg = []
    for idx, inp in enumerate(m.get('input_files', []) or []):
        p = resolve_path(base_dir, inp.get('path',''))
        if not p or not p.exists():
            input_ok = False
            input_msg.append(f'input_files[{idx}] missing: {inp.get("path","")}')
            continue
        actual_sha = sha256_file(p)
        if inp.get('sha256') and actual_sha != inp.get('sha256'):
            input_ok = False
            input_msg.append(f'input_files[{idx}] sha256 mismatch')
        actual_rows, actual_cols = csv_row_col_count(p)
        if inp.get('rows') and int(inp.get('rows')) != actual_rows:
            input_ok = False
            input_msg.append(f'input_files[{idx}] rows {actual_rows} != manifest {inp.get("rows")}')
        if inp.get('cols') and int(inp.get('cols')) != actual_cols:
            input_ok = False
            input_msg.append(f'input_files[{idx}] cols {actual_cols} != manifest {inp.get("cols")}')
    results['input_integrity'] = check('input_integrity', input_ok, '; '.join(input_msg) if input_msg else 'ok')

    # 1c. sample_flow non-empty and consistent
    sf = m.get('sample_flow', {}) or {}
    sf_ok = True
    sf_msg = []
    for k in ['raw','after_qc','train','validation','test','external']:
        v = sf.get(k)
        if v is None or v == '':
            sf_ok = False
            sf_msg.append(f'sample_flow.{k} empty')
    results['sample_flow_non_empty'] = check('sample_flow_non_empty', sf_ok, '; '.join(sf_msg) if sf_msg else 'ok')

    # 2. endpoint_indicator_match
    st = m.get('study_type','')
    ep = True
    msgs = []
    if st == 'diagnostic':
        if metrics.get('auc') is None:
            ep = False; msgs.append('diagnostic requires auc')
        if all(metrics.get(k) is None for k in ['sensitivity','specificity','npv','ppv']):
            ep = False; msgs.append('diagnostic requires sensitivity/specificity or ppv/npv')
        if any(metrics.get(k) is not None for k in ['c_index','hr','or']):
            ep = False; msgs.append('diagnostic should not report c_index/hr/or as primary')
    elif st == 'prognostic':
        if all(metrics.get(k) is None for k in ['c_index','time_dependent_auc','hr']):
            ep = False; msgs.append('prognostic requires c_index or time_dependent_auc or hr')
        if not m.get('truth_source'):
            ep = False; msgs.append('prognostic requires truth_source')
        if not m.get('censoring_def'):
            ep = False; msgs.append('prognostic requires censoring_def')
    elif st == 'treatment_effect':
        if all(metrics.get(k) is None for k in ['hr','or','rd','md']):
            ep = False; msgs.append('treatment_effect requires hr/or/rd/md')
    elif st == 'systematic_review':
        if metrics.get('i2') is None:
            ep = False; msgs.append('systematic_review requires i2')
    results['endpoint_indicator_match'] = check('endpoint_indicator_match', ep, '; '.join(msgs) if msgs else 'ok')

    # 3. numbers_consistency + HTML vs metrics numeric consistency
    raw = sf.get('raw', 0)
    after_qc = sf.get('after_qc', 0)
    splits = sf.get('train',0) + sf.get('validation',0) + sf.get('test',0) + sf.get('external',0)
    nc = True
    nc_msgs = []
    if raw <= 0:
        nc = False; nc_msgs.append('raw<=0')
    if after_qc <= 0:
        nc = False; nc_msgs.append('after_qc<=0')
    if after_qc > raw:
        nc = False; nc_msgs.append('after_qc > raw')
    if splits > after_qc:
        nc = False; nc_msgs.append(f'splits {splits} > after_qc {after_qc}')
    missing_artifacts = [a for a in m.get('artifacts', []) if not resolve_path(base_dir, a) or not resolve_path(base_dir, a).exists()]
    if missing_artifacts:
        nc = False; nc_msgs.append(f'missing artifacts: {missing_artifacts}')
    ms = m.get('model_spec', {}) or {}
    feats = ms.get('features', [])
    coefs = ms.get('coefficients', [])
    if feats and coefs and len(feats) != len(coefs):
        nc = False; nc_msgs.append('coefficients length != features length')
    # HTML vs metrics numeric consistency (scalar metrics only, reject invalid placeholders)
    for a in m.get('artifacts', []) or []:
        ap = resolve_path(base_dir, a)
        if ap and ap.exists() and ap.suffix.lower() == '.html':
            txt = ap.read_text(encoding='utf-8', errors='ignore')
            for key, val in metrics.items():
                if not is_valid_metric(val):
                    continue
                pattern = re.compile(rf'{re.escape(key)}\b.*?([0-9]+(?:\.[0-9]+)?)', re.IGNORECASE)
                m_match = pattern.search(txt)
                if not m_match:
                    nc = False
                    nc_msgs.append(f'HTML missing metric {key}')
                    continue
                html_val = float(m_match.group(1))
                if abs(float(val) - html_val) > 0.001:
                    nc = False
                    nc_msgs.append(f'HTML metric {key} {html_val} != manifest {val}')
    results['numbers_consistency'] = check('numbers_consistency', nc, '; '.join(nc_msgs) if nc_msgs else 'ok')

    # 4. censoring_encoding
    c_ok = True
    c_msg = []
    cdef = m.get('censoring_def','')
    if st in ('prognostic','treatment_effect') and not cdef:
        c_ok = False; c_msg.append('censoring_def missing for survival study')
    input_files = m.get('input_files', []) or []
    col_map = m.get('column_map', {}) or {}
    event_col = col_map.get('event','')
    if input_files and event_col:
        data_path = resolve_path(base_dir, input_files[0].get('path',''))
        if data_path and data_path.exists():
            with open(data_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if event_col in (reader.fieldnames or []):
                    vals = set()
                    for row in reader:
                        vals.add(row[event_col])
                    allowed = {'0','1','0.0','1.0'}
                    if not vals.issubset(allowed):
                        c_ok = False; c_msg.append(f'event column has invalid values: {vals}')
                else:
                    c_ok = False; c_msg.append(f'event column {event_col} not in data')
        else:
            c_msg.append('input data file not found, skip censoring check')
    results['censoring_encoding'] = check('censoring_encoding', c_ok, '; '.join(c_msg) if c_msg else 'ok')

    # 5. train_val_isolation
    split = m.get('split_manifest', {}) or {}
    sets = {}
    overlap_ok = True
    split_msg = []
    for k in ['train','validation','test','external']:
        ids = split.get(k, [])
        sets[k] = set(ids)
        if not ids:
            split_msg.append(f'{k} empty')
    keys = list(sets.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            if sets[keys[i]] & sets[keys[j]]:
                overlap_ok = False
                split_msg.append(f'overlap between {keys[i]} and {keys[j]}')
    total_ids = sum(len(v) for v in sets.values())
    if raw > 0 and total_ids > raw:
        overlap_ok = False
        split_msg.append(f'total split ids {total_ids} > raw {raw}')
    results['train_val_isolation'] = check('train_val_isolation', overlap_ok, '; '.join(split_msg) if split_msg else 'ok')

    # 6. no_fictional_external
    ext = m.get('external_validation', {}) or {}
    ext_status = ext.get('status', 'unavailable')
    ext_ok = True
    ext_msg = []
    if ext_status == 'completed':
        ext_path = resolve_path(base_dir, ext.get('external_data_path',''))
        ext_ids = ext.get('external_ids', [])
        ext_metrics = ext.get('external_metrics', {}) or {}
        if not ext_path or not ext_path.exists():
            ext_ok = False; ext_msg.append('external_data_path missing or file not found')
        if not ext_ids:
            ext_ok = False; ext_msg.append('external_ids empty')
        if all(v is None for v in ext_metrics.values()):
            ext_ok = False; ext_msg.append('external_metrics empty')
        ext_id_set = set(ext_ids)
        for k in ['train','validation','test']:
            if ext_id_set & sets.get(k, set()):
                ext_ok = False; ext_msg.append(f'external ids overlap with {k}')
                break
    results['no_fictional_external'] = check('no_fictional_external', ext_ok, '; '.join(ext_msg) if ext_msg else 'ok')

    # 7. no_unsubstantiated_clinical_claims
    claim_ok = True
    claim_msg = []
    dm = m.get('data_mode','real')
    report_paths = [a for a in m.get('artifacts', []) if isinstance(a, str) and a.lower().endswith('.html')]
    if dm == 'simulated':
        found_demo = False
        for rp in report_paths:
            rp_abs = resolve_path(base_dir, rp)
            if rp_abs and rp_abs.exists():
                txt = rp_abs.read_text(encoding='utf-8', errors='ignore')
                if 'DEMO' in txt or '模拟数据' in txt:
                    found_demo = True
                banned = ['可用于临床决策', '建议临床采用', '证据强度高', '可指导临床', 'robust prognostic tool', 'guideline-level evidence']
                hits = [b for b in banned if b in txt]
                if hits:
                    claim_ok = False
                    claim_msg.append(f'banned phrases in {rp}: {hits}')
        if report_paths and not found_demo:
            claim_ok = False
            claim_msg.append('simulated data report missing DEMO banner')
    elif dm == 'real':
        if report_paths and m.get('human_sign_off') != True:
            rp0 = resolve_path(base_dir, report_paths[0])
            txt = rp0.read_text(encoding='utf-8', errors='ignore') if rp0 and rp0.exists() else ''
            banned = ['可用于临床决策', '建议临床采用', 'evidence supports clinical use']
            if any(b in txt for b in banned):
                claim_ok = False
                claim_msg.append('real data report contains clinical claims without human_sign_off')
    results['no_unsubstantiated_clinical_claims'] = check('no_unsubstantiated_clinical_claims', claim_ok, '; '.join(claim_msg) if claim_msg else 'ok')

    # 8. metric validity (scalar performance metrics only; list/array metrics are validated elementwise)
    scalar_metric_keys = {'auc', 'c_index', 'time_dependent_auc', 'brier', 'sensitivity', 'specificity', 'ppv', 'npv', 'or', 'i2'}
    invalid_metrics = []
    for key, val in metrics.items():
        if key not in scalar_metric_keys:
            continue
        if isinstance(val, list):
            if any(not is_valid_metric(v) for v in val):
                invalid_metrics.append(key)
            continue
        if val is None:
            continue
        if not is_valid_metric(val):
            invalid_metrics.append(key)
    results['metric_validity'] = check('metric_validity', not invalid_metrics, f'invalid metrics: {invalid_metrics}' if invalid_metrics else 'all metrics valid')

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nSummary: {passed}/{total} passed")
    return results, passed == total

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--json', default=None, help='path to write machine-readable results JSON')
    ap.add_argument('--metrics-policy', default='strict', choices=['strict','manifest_wins','disk_wins'], help='metrics conflict resolution policy')
    args = ap.parse_args()
    results, ok = run(args.manifest, metrics_policy=args.metrics_policy)
    if args.json:
        Path(args.json).write_text(json.dumps({"results": results, "passed": ok}, ensure_ascii=False), encoding='utf-8')
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
