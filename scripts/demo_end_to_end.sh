#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
WORK=$(mktemp -d /tmp/mdm_e2e_XXXXXX)
echo "TEST_DIR=$WORK"

# 1) Diagnostic (logistic)
cat > "$WORK/input_diag.csv" <<'CSV'
id,age,sex,bmi,outcome
D01,60,1,25,1
D02,55,0,22,0
D03,70,1,28,1
D04,50,0,21,0
D05,65,1,27,1
D06,58,0,24,0
D07,72,1,30,1
D08,49,0,20,0
D09,66,1,26,1
D10,52,0,23,0
CSV

python3 scripts/setup_project.py \
  --study-type diagnostic \
  --output "$WORK/diag_project" \
  --data "$WORK/input_diag.csv" \
  --id-col id \
  --outcome-col outcome
DIAG_SETUP_EXIT=$?

python3 scripts/run_workflow.py --manifest "$WORK/diag_project/manifest.json" --train --plots
DIAG_TRAIN_EXIT=$?

# 2) Prognostic (Cox PH)
cat > "$WORK/input_prog.csv" <<'CSV'
id,time,event,age,stage
P001,12,1,65,3
P002,18,0,58,2
P003,24,1,72,4
P004,30,0,61,2
P005,36,1,68,3
P006,42,0,55,1
P007,48,1,74,4
P008,54,0,60,2
P009,60,1,69,3
P010,66,0,63,2
CSV

python3 scripts/setup_project.py \
  --study-type prognostic \
  --output "$WORK/prog_project" \
  --data "$WORK/input_prog.csv" \
  --id-col id \
  --time-col time \
  --event-col event
PROG_SETUP_EXIT=$?

python3 scripts/run_workflow.py --manifest "$WORK/prog_project/manifest.json" --train --plots
PROG_TRAIN_EXIT=$?

# 3) External validation data
cat > "$WORK/external.csv" <<'CSV'
id,time,event,age,stage
E01,14,1,63,3
E02,20,0,57,2
E03,27,1,70,4
E04,33,0,59,2
E05,40,1,66,3
CSV

python3 - "$WORK/prog_project/manifest.json" "$WORK/external.csv" <<'PY'
import json, sys
from pathlib import Path
manifest_path = Path(sys.argv[1]).resolve()
external_path = Path(sys.argv[2]).resolve()
m = json.loads(manifest_path.read_text(encoding='utf-8'))
m['external_validation']['status'] = 'pending'
m['external_validation']['external_data_path'] = str(external_path)
manifest_path.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding='utf-8')
print('Manifest updated:')
print(json.dumps(m['external_validation'], indent=2))
PY

python3 scripts/run_workflow.py --manifest "$WORK/prog_project/manifest.json" --external-validation
EXTVAL_EXIT=$?

# 4) Unit tests
python3 -B -m unittest discover -s tests -v
TESTS_EXIT=$?

cat <<EOF
=== PROOF ===
TEST_DIR=$WORK
DIAG_SETUP_EXIT=$DIAG_SETUP_EXIT
DIAG_TRAIN_EXIT=$DIAG_TRAIN_EXIT
PROG_SETUP_EXIT=$PROG_SETUP_EXIT
PROG_TRAIN_EXIT=$PROG_TRAIN_EXIT
EXTVAL_EXIT=$EXTVAL_EXIT
TESTS_EXIT=$TESTS_EXIT
EOF
