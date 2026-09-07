#!/usr/bin/env python3
"""
Project setup wizard for medical-data-mining skill.

Creates a new study directory from templates and fills basic manifest fields
by asking the user a few questions.

Usage:
  python3 scripts/setup_project.py --study-type diagnostic --output ~/my_study
  python3 scripts/setup_project.py --study-type prognostic --output ~/my_study --data data.csv --id-col id --time-col time --event-col event
"""
import argparse, hashlib, json, csv, sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"


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


def copy_template(study_type, output_dir):
    src = TEMPLATES_DIR / study_type
    if not src.exists():
        print(f"FAIL: template not found: {src}")
        sys.exit(1)
    dst = Path(output_dir).resolve()
    if dst.exists():
        print(f"FAIL: output directory already exists: {dst}")
        sys.exit(1)
    import shutil
    shutil.copytree(src, dst)
    return dst


def infer_split_from_data(data_path, id_col='id', event_col='event', train_ratio=0.8, seed=42):
    ids, events = [], []
    with open(data_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids.append(row[id_col])
            events.append(int(row.get(event_col, '0')))
    ids_unique = sorted(set(ids))
    event_ids = [id_ for id_, e in zip(ids, events) if e == 1]
    nonevent_ids = [id_ for id_, e in zip(ids, events) if e == 0]
    def _split(lst, ratio):
        k = max(1, int(ratio * len(lst)))
        if k == 0:
            k = 1
        if k >= len(lst):
            k = len(lst) - 1
        return lst[:k], lst[k:]
    train_event, val_event = _split(event_ids, train_ratio)
    train_nonevent, val_nonevent = _split(nonevent_ids, train_ratio)
    train = sorted(train_event + train_nonevent)
    val = sorted(val_event + val_nonevent)
    if not train:
        train = ids_unique[:1]
        val = [i for i in ids_unique if i not in train]
    if not val:
        val = ids_unique[-1:]
        train = [i for i in ids_unique if i not in val]
    return sorted(train), sorted(val)


def update_manifest(dst, args):
    manifest_path = dst / "manifest.json"
    m = load_json(manifest_path)
    m['study_type'] = args.study_type
    if args.data:
        data_path = Path(args.data).resolve()
        if not data_path.exists():
            print(f"FAIL: data file not found: {data_path}")
            sys.exit(1)
        dst_data = dst / "data.csv"
        import shutil
        shutil.copy2(data_path, dst_data)
        m['input_files'] = [{
            "path": "data.csv",
            "sha256": sha256_file(dst_data),
            "rows": csv_row_col_count(dst_data)[0],
            "cols": csv_row_col_count(dst_data)[1],
            "description": "user provided cohort"
        }]
        # auto populate split / sample flow when empty
        split = m.get('split_manifest', {}) or {}
        train_ids = split.get('train', [])
        val_ids = split.get('validation', [])
        id_col = args.id_col or m.get('column_map', {}).get('id', 'id')
        if not train_ids or not val_ids:
            train_ids, val_ids = infer_split_from_data(dst_data, id_col)
        m['split_manifest'] = {
            'train': sorted(train_ids),
            'validation': sorted(val_ids),
            'test': split.get('test', []),
            'external': split.get('external', [])
        }
        total = len(train_ids) + len(val_ids)
        sf = m.get('sample_flow', {}) or {}
        sf['raw'] = total
        sf['after_qc'] = total
        sf['train'] = len(train_ids)
        sf['validation'] = len(val_ids)
        sf['test'] = len(split.get('test', []))
        sf['external'] = len(split.get('external', []))
        m['sample_flow'] = sf
    if args.id_col:
        m.setdefault('column_map', {})['id'] = args.id_col
    if args.outcome_col:
        m.setdefault('column_map', {})['outcome'] = args.outcome_col
    if args.time_col:
        m.setdefault('column_map', {})['time'] = args.time_col
    if args.event_col:
        m.setdefault('column_map', {})['event'] = args.event_col
    if args.study_type in ('prognostic', 'treatment_effect') and args.data:
        data_path = Path(args.data).resolve()
        with open(data_path, newline='', encoding='utf-8') as f:
            header = next(csv.reader(f))
        id_col = m.get('column_map', {}).get('id', args.id_col)
        time_col = m.get('column_map', {}).get('time', args.time_col)
        event_col = m.get('column_map', {}).get('event', args.event_col)
        feature_cols = [c for c in header if c not in (id_col, time_col, event_col, 'outcome')]
        m.setdefault('model_spec', {})['features'] = feature_cols
    # auto-fill truth_source when empty
    if not m.get('truth_source'):
        m['truth_source'] = {
            'diagnostic': 'outcome',
            'prognostic': 'simulated_events',
            'treatment_effect': 'simulated_events',
            'systematic_review': 'published'
        }.get(m.get('study_type'), 'unspecified')
    save_json(manifest_path, m)
    return manifest_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--study-type', required=True, choices=['diagnostic', 'prognostic', 'treatment_effect', 'systematic_review'])
    ap.add_argument('--output', required=True)
    ap.add_argument('--data', default=None)
    ap.add_argument('--id-col', default='id')
    ap.add_argument('--outcome-col', default='outcome')
    ap.add_argument('--time-col', default='')
    ap.add_argument('--event-col', default='')
    args = ap.parse_args()

    dst = copy_template(args.study_type, args.output)
    manifest_path = update_manifest(dst, args)
    print('created project:', dst)
    print('manifest:', manifest_path)


if __name__ == '__main__':
    main()
