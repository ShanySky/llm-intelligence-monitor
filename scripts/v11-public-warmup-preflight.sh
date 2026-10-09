#!/usr/bin/env bash
set -euo pipefail

# Check offline dependency availability and unchanged official reference behavior
# without starting any model. Gold and test patches arrive AFTER warmup and
# offline smoke testing, on this throwaway verifier-only container.
CASE_ID="${CASE_ID:?required}"
DIR="v11-warmup-preflight"
mkdir -p "$DIR"
C=""
START=$(date +%s)
STAGE="metadata"
PRIME_EXIT=999
BASELINE_EXIT=999
REFERENCE_EXIT=999
cleanup() {
  local result=$?
  if [[ -n "$C" ]]; then docker rm -f "$C" >/dev/null 2>&1 || true; fi
  RESULT_CASE="$CASE_ID" RESULT_STAGE="$STAGE" RESULT_EXIT="$result" RESULT_PRIME="$PRIME_EXIT" RESULT_BASELINE="$BASELINE_EXIT" RESULT_REFERENCE="$REFERENCE_EXIT" RESULT_START="$START" python3 - <<'PY'
import json,os,time
from pathlib import Path
def x(k):return os.getenv("RESULT_"+k,"")
valid=x("EXIT")=="0" and x("PRIME")=="0" and int(x("BASELINE")) not in (0,124,137,999) and x("REFERENCE")=="0"
obj={"task":x("CASE"),"status":"offline_agent_ready" if valid else "not_ready",
     "stage":x("STAGE"),"prime_exit_code":int(x("PRIME")),
     "offline_baseline_exit_code":int(x("BASELINE")),
     "offline_reference_exit_code":int(x("REFERENCE")),
     "agent_network_after_warmup":"none",
     "model_calls":0,"elapsed_seconds":int(time.time())-int(x("START")),
     "note":"Reference/test patches are introduced only after source-only warmup and existing-test smoke; never in agent workspace."}
p=Path("v11-warmup-preflight/result.json")
p.write_text(json.dumps(obj,indent=2)+"\n")
print(json.dumps(obj,indent=2))
PY
  exit "$result"
}
trap cleanup EXIT
read -r BASE REV < <(CASE_ID="$CASE_ID" python3 - <<'PY'
import json,os
from pathlib import Path
m=json.loads(Path("benchmarks/v1.1-public-candidates.json").read_text())
t=next((x for x in m["source_candidates"] if x["id"]==os.environ["CASE_ID"]),None)
assert t and t["environment_status"]=="environment_ready" and t["reference_test_status"]=="baseline_failed_reference_passed"
assert os.environ["CASE_ID"] in ("google__gson-1093","vuejs__core-11739")
print(t["base_commit"],m["dataset_pinned_revision"])
PY
)
STAGE="download-official-assets"
ROOT="https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$REV/tasks/$CASE_ID"
for file in task.yaml eval.sh gold.patch; do
  curl --fail --silent --show-error --retry 2 --max-time 45 "$ROOT/$file" -o "$DIR/$file"
done
IMAGE=$(sed -n 's/^image: //p' "$DIR/task.yaml" | tr -d '\r')
PIN=$(sed -n 's/^base_commit: //p' "$DIR/task.yaml" | tr -d '\r')
test "$PIN" = "$BASE"
[[ "$IMAGE" == swebench/sweb.eval.x86_64.* ]]
STAGE="image"
timeout 160s docker pull "$IMAGE" > "$DIR/pull.log" 2>&1
C="v11-warm-${GITHUB_RUN_ID:-local}-$(echo "$CASE_ID" | tr '_' '-')"
docker run -d --name "$C" --network bridge --cap-drop ALL --security-opt no-new-privileges --memory 4g --cpus 2 "$IMAGE" sleep infinity >/dev/null
docker exec -w /testbed "$C" git reset --hard "$BASE" > "$DIR/reset.log" 2>&1
test "$(docker exec -w /testbed "$C" git rev-parse HEAD | tr -d '\r')" = "$BASE"
STAGE="warm-then-disconnect"
export AGENT_DOCKER_CONTAINER="$C" BASE_COMMIT="$BASE" WARMUP_LOG_DIR="$DIR"
bash scripts/v11-public-agent-deps.sh
PRIME_EXIT=0
STAGE="offline-baseline"
docker cp "$DIR/eval.sh" "$C:/tmp/v11-eval.sh"
set +e
timeout 220s docker exec -w /testbed "$C" bash -e /tmp/v11-eval.sh > "$DIR/official-baseline.log" 2>&1
BASELINE_EXIT=$?
set -e
if [[ "$BASELINE_EXIT" == 0 || "$BASELINE_EXIT" == 124 || "$BASELINE_EXIT" == 137 ]]; then
  echo "Offline base test did not fail as expected" >&2
  exit 1
fi
STAGE="offline-reference"
docker exec -w /testbed "$C" git reset --hard "$BASE" >/dev/null
docker cp "$DIR/gold.patch" "$C:/tmp/v11-gold.patch"
docker exec -w /testbed "$C" git apply /tmp/v11-gold.patch
set +e
timeout 220s docker exec -w /testbed "$C" bash -e /tmp/v11-eval.sh > "$DIR/official-reference.log" 2>&1
REFERENCE_EXIT=$?
set -e
if [[ "$REFERENCE_EXIT" != 0 ]]; then
  echo "::group::Offline reference failure $CASE_ID"
  tail -n 65 "$DIR/official-reference.log"
  echo "::endgroup::"
  exit 1
fi
STAGE="completed"
