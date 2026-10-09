#!/usr/bin/env bash
set -euo pipefail

# An official-source, NO-MODEL-CALL reproducibility test. Never expose upstream gold/test patches to an agent workspace.
CASE_ID="${CASE_ID:-google__gson-2311}"
REPORT_DIR="v11-public-env-preflight"
mkdir -p "$REPORT_DIR"
START=$(date +%s)
IMAGE=""
BASE=""
COMMIT=""
C=""
STAGE="metadata"
BASELINE_EXIT=999
REFERENCE_EXIT=999
IMAGE_READY=false
PATCH_READY=false
EVALUATOR_READY=false

finish() {
  local status=$?
  if [[ -n "$C" ]]; then docker rm -f "$C" >/dev/null 2>&1 || true; fi
  RESULT_STAGE="$STAGE" RESULT_STATUS="$status" RESULT_CASE="$CASE_ID" RESULT_IMAGE="$IMAGE" RESULT_BASE="$BASE" RESULT_COMMIT="$COMMIT" RESULT_BASELINE="$BASELINE_EXIT" RESULT_REFERENCE="$REFERENCE_EXIT" RESULT_START="$START" RESULT_IMAGE_READY="$IMAGE_READY" RESULT_PATCH_READY="$PATCH_READY" RESULT_EVALUATOR_READY="$EVALUATOR_READY" python3 - <<'PY'
import json,os,time
from pathlib import Path
def env(k): return os.environ.get("RESULT_"+k,"")
base_exit=int(env("BASELINE"))
reference_exit=int(env("REFERENCE"))
complete=(env("STATUS")=="0" and base_exit not in (0,124,137,999) and reference_exit==0)
obj={
  "task":env("CASE"),"source":"SWE-bench Multilingual",
  "upstream_commit":env("COMMIT"),"base_commit":env("BASE"),"image":env("IMAGE"),
  "status":"environment_ready" if complete else "incomplete_environment",
  "stage":env("STAGE"),"network_mode":"bridge","image_ready":env("IMAGE_READY")=="true",
  "test_patch_and_ref_applied":env("PATCH_READY")=="true",
  "evaluator_ready":env("EVALUATOR_READY")=="true",
  "baseline_exit_code":base_exit,"reference_exit_code":reference_exit,
  "baseline_expected_to_fail":base_exit not in (0,124,137,999),
  "reference_expected_to_pass":reference_exit==0,
  "duration_seconds":int(time.time())-int(env("START")),"model_calls":0,
  "note":"Evaluator runs with network access for dependency resolution after any model work; no model calls in this reference check."
}
out=Path("v11-public-env-preflight/result.json")
out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(obj,ensure_ascii=False,indent=2))
PY
  exit "$status"
}
trap finish EXIT

STAGE="download-upstream"
# Parse ONLY a task id from the preverified list; do not accept arbitrary shell paths.
IFS=$'\t' read -r BASE COMMIT <<EOF
$(CASE="$CASE_ID" python3 - <<'PY'
import os,json
from pathlib import Path
m=json.loads(Path("benchmarks/v1.1-public-candidates.json").read_text())
row=next((x for x in m["source_candidates"] if x["id"]==os.environ["CASE"] and x["priority"] in ("A","B")),None)
if not row: raise SystemExit("Not an admitted first-stage candidate")
print(row["base_commit"]+"\t"+m["dataset_pinned_revision"])
PY
)
EOF
UPSTREAM="https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$COMMIT/tasks/$CASE_ID"
mkdir -p "$REPORT_DIR/upstream"
for asset in task.yaml eval.sh gold.patch test.patch tests.json; do
  curl --retry 2 --max-time 45 --fail --silent --show-error "$UPSTREAM/$asset" -o "$REPORT_DIR/upstream/$asset"
done
IMAGE=$(sed -n 's/^image: //p' "$REPORT_DIR/upstream/task.yaml" | tr -d '\r')
PIN=$(sed -n 's/^base_commit: //p' "$REPORT_DIR/upstream/task.yaml" | tr -d '\r')
test "$PIN" = "$BASE"
test -n "$IMAGE"
python3 -m json.tool "$REPORT_DIR/upstream/tests.json" >/dev/null

STAGE="pull-official-image"
timeout 180s docker pull "$IMAGE" > "$REPORT_DIR/pull.log" 2>&1
IMAGE_READY=true
STAGE="start-official-image"
C="v11-public-${GITHUB_RUN_ID:-local}"
docker run -d --network bridge --name "$C" "$IMAGE" sleep infinity >/dev/null
docker exec "$C" test -d /testbed

STAGE="copy-upstream-evaluator"
docker exec "$C" mkdir -p /tmp/v11
for asset in eval.sh gold.patch test.patch; do
  docker cp "$REPORT_DIR/upstream/$asset" "$C:/tmp/v11/$asset"
done
EVALUATOR_READY=true

STAGE="baseline-evaluation"
docker exec -w /testbed "$C" git reset --hard "$BASE" > "$REPORT_DIR/reset-baseline.log" 2>&1
set +e
timeout 200s docker exec -w /testbed "$C" bash -e /tmp/v11/eval.sh > "$REPORT_DIR/baseline.log" 2>&1
BASELINE_EXIT=$?
set -e
if [[ "$BASELINE_EXIT" == 0 || "$BASELINE_EXIT" == 124 || "$BASELINE_EXIT" == 137 ]]; then
  echo "Baseline did not produce a valid failing test result" >&2
  exit 1
fi

STAGE="reference-evaluation"
docker exec -w /testbed "$C" git reset --hard "$BASE" > "$REPORT_DIR/reset-reference.log" 2>&1
docker exec -w /testbed "$C" git apply /tmp/v11/gold.patch > "$REPORT_DIR/apply-reference.log" 2>&1
PATCH_READY=true
set +e
timeout 200s docker exec -w /testbed "$C" bash -e /tmp/v11/eval.sh > "$REPORT_DIR/reference.log" 2>&1
REFERENCE_EXIT=$?
set -e
if [[ "$REFERENCE_EXIT" != 0 ]]; then
  echo "::group::Reference failure diagnosis for $CASE_ID (exit=$REFERENCE_EXIT)"
  echo "---- reference evaluator last 65 lines ----"
  tail -n 65 "$REPORT_DIR/reference.log" || true
  echo "---- dependency / test failure signatures ----"
  grep -iE 'unknown host|not found|could not (resolve|download|transfer|find|collect)|no such file|network is unreachable|temporary failure|unable to get|npm err|failed to|compilation failure|test failures|error' "$REPORT_DIR/reference.log" | tail -n 55 || true
  echo "::endgroup::"
  exit 1
fi
STAGE="completed"
