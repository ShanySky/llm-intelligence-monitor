#!/usr/bin/env bash
set -euo pipefail
# Re-evaluate a previously saved model patch: ZERO model calls.
# Network is enabled for the VERIFIER only; the original model execution was isolated.
CASE_ID="${CASE_ID:?Missing case}"
INPUT_DIR="${INPUT_DIR:-v11-regrade-input}"
OUTDIR="v11-regrade"
mkdir -p "$OUTDIR"
C=""
STAGE="verify-admission"
EVAL_EXIT=999
ORIGINAL_SCORE=""
ORIGINAL_RUN=""
PATCH_STATUS="not-checked"
START=$(date +%s)
finish() {
  local code=$?
  if [[ -n "$C" ]]; then docker rm -f "$C" >/dev/null 2>&1 || true; fi
  RESULT_CASE="$CASE_ID" RESULT_STAGE="$STAGE" RESULT_EXIT="$code" RESULT_EVAL="$EVAL_EXIT" RESULT_ORIGINAL="$ORIGINAL_SCORE" RESULT_ORIGINAL_RUN="$ORIGINAL_RUN" RESULT_PATCH="$PATCH_STATUS" RESULT_START="$START" python3 - <<'PY'
import json,os,re,time
from pathlib import Path
def env(x): return os.environ.get("RESULT_"+x,"")
e=int(env("EVAL"));status=int(env("EXIT"))
log=Path("v11-regrade/official-eval.log")
s=log.read_text(errors="replace") if log.exists() else ""
infra=bool(re.search(r"(?i)EAI_AGAIN|ENOTFOUND|Unknown host|Temporary failure in name resolution|Could not transfer artifact|Could not resolve host|Network is unreachable|Connection refused.*(?:repo|registry)",s))
ready=status==0 and e not in (999,124,137) and not infra
d={"task":env("CASE"),"model":"gpt-6-luna","effort":"high","source":"SWE-bench Multilingual",
   "reference_admission":"official baseline fails, gold passes in connected evaluator",
   "agent_network":"none","evaluator_network":"bridge",
   "model_calls":0,"original_run_id":int(env("ORIGINAL_RUN") or 0),
   "original_score":int(env("ORIGINAL")) if env("ORIGINAL") not in ("","null") else None,
   "score":(100 if e==0 else 0) if ready else None,
   "data_complete":ready,"verifier_exit_code":e,
   "classification":("official-resolved" if e==0 else "official-unresolved") if ready else "invalid-infrastructure-or-patch",
   "stage":env("STAGE"),"model_patch_status":env("PATCH"),
   "duration_seconds":int(time.time())-int(env("START")),
   "infrastructure_failure_signature":infra}
Path("v11-regrade/result.json").write_text(json.dumps(d,indent=2)+"\n")
print(json.dumps(d,indent=2))
PY
  exit "$code"
}
trap finish EXIT

test -f "$INPUT_DIR/model.patch"
test -f "$INPUT_DIR/result.json"
read -r BASE SHA SOURCE_RUN ORIG < <(CASE_ID="$CASE_ID" INPUT_DIR="$INPUT_DIR" python3 - <<'PY'
import json,os
from pathlib import Path
manifest=json.loads(Path("benchmarks/v1.1-public-candidates.json").read_text())
r=json.loads((Path(os.environ["INPUT_DIR"])/"result.json").read_text())
case=os.environ["CASE_ID"]
entry=next((t for t in manifest["source_candidates"] if t["id"]==case),None)
assert entry is not None and entry.get("environment_validation")
assert r["task"]==case and r["model"]=="gpt-6-luna" and r["effort"]=="high"
assert r["data_complete"] and r["base_commit"]==entry["base_commit"]
assert r["score"] in (0,100)
print(entry["base_commit"],manifest["dataset_pinned_revision"],entry["environment_validation"]["run_id"],r["score"])
PY
)
ORIGINAL_SCORE="$ORIG"
ORIGINAL_RUN="${ORIGINAL_RUN_ID:-0}"
case "$CASE_ID" in
  google__gson-2158) ORIGINAL_RUN=37758488863;;
  google__gson-2311|axios__axios-5316) ORIGINAL_RUN=37759079285;;
  *) echo "Task not admitted to this regrade batch" >&2;exit 1;;
esac
STAGE="verify-reference-parity"
test -f v11-public-env-preflight/result.json
python3 - <<'PY'
import json,os
from pathlib import Path
r=json.loads(Path("v11-public-env-preflight/result.json").read_text())
assert r["task"]==os.environ["CASE_ID"] and r["status"]=="environment_ready"
assert r["reference_exit_code"]==0 and r["baseline_exit_code"] not in (0,124,137,999)
assert r["network_mode"]=="bridge"
PY
STAGE="download-original-evaluator"
UP="https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$SHA/tasks/$CASE_ID"
curl -fsSL --retry 2 --max-time 45 "$UP/task.yaml" -o "$OUTDIR/task.yaml"
curl -fsSL --retry 2 --max-time 45 "$UP/eval.sh" -o "$OUTDIR/eval.sh"
test "$(sed -n 's/^base_commit: //p' "$OUTDIR/task.yaml" | tr -d '\r')" = "$BASE"
IMAGE="$(sed -n 's/^image: //p' "$OUTDIR/task.yaml" | tr -d '\r')"
[[ "$IMAGE" == swebench/sweb.eval.x86_64.* ]]
STAGE="prepare-connected-verifier"
timeout 150s docker pull "$IMAGE" > "$OUTDIR/pull.log" 2>&1
C="v11-regrade-${GITHUB_RUN_ID:-local}-$(echo "$CASE_ID" | tr '_' '-')"
docker run -d --name "$C" --network bridge --cap-drop ALL --security-opt no-new-privileges --memory 4g --cpus 2 "$IMAGE" sleep infinity >/dev/null
docker exec -w /testbed "$C" git reset --hard "$BASE" > "$OUTDIR/reset.log" 2>&1
if [[ -s "$INPUT_DIR/model.patch" ]]; then
  STAGE="apply-preserved-model-patch"
  docker cp "$INPUT_DIR/model.patch" "$C:/tmp/model.patch"
  docker exec -w /testbed "$C" git apply --check /tmp/model.patch
  docker exec -w /testbed "$C" git apply /tmp/model.patch
  PATCH_STATUS="applied"
else
  PATCH_STATUS="empty-original-patch"
fi
sha256sum "$INPUT_DIR/model.patch" > "$OUTDIR/patch.sha256"
docker cp "$OUTDIR/eval.sh" "$C:/tmp/v11-eval.sh"
STAGE="run-connected-official-evaluator"
set +e
timeout 240s docker exec -w /testbed "$C" bash -e /tmp/v11-eval.sh > "$OUTDIR/official-eval.log" 2>&1
EVAL_EXIT=$?
set -e
if [[ "$EVAL_EXIT" == 124 || "$EVAL_EXIT" == 137 ]];then
  tail -n 50 "$OUTDIR/official-eval.log" || true
  exit 1
fi
if [[ "$EVAL_EXIT" != 0 ]];then
  echo "::group::Official verifier failure for $CASE_ID"
  tail -n 45 "$OUTDIR/official-eval.log" || true
  echo "::endgroup::"
fi
STAGE="completed"
