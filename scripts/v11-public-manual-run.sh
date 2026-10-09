#!/usr/bin/env bash
set -euo pipefail

# Explicit manual one-case public engineering evaluation; never invoked by default.
OUTDIR="v11-public-manual"
mkdir -p "$OUTDIR"
STAGE="admission"
START=$(date +%s)
CASE=""
BASE=""
IMAGE=""
UPSTREAM_COMMIT=""
C=""
VC=""
MODEL_STARTED=false
RUNNER_EXIT=999
EVAL_EXIT=999
RUNNER_FILE=""
AGENT_WALL=540
MODEL_ID="${MODEL_ID:?MODEL_ID required}"
REASONING_EFFORT="${REASONING_EFFORT:?REASONING_EFFORT required}"
case "$MODEL_ID" in gpt-6-luna|gpt-6.1-sol) ;; *) echo "Unsupported model"; exit 2;; esac
case "$REASONING_EFFORT" in medium|high|xhigh) ;; *) echo "Unsupported effort"; exit 2;; esac
RESULT_STATUS="incomplete_environment"

finalize() {
  local shell_exit=$?
  if [[ -n "$C" ]]; then docker rm -f "$C" >/dev/null 2>&1 || true; fi
  if [[ -n "$VC" ]]; then docker rm -f "$VC" >/dev/null 2>&1 || true; fi
  STAGE="$STAGE" CASE="$CASE" BASE="$BASE" IMAGE="$IMAGE" UPSTREAM_COMMIT="$UPSTREAM_COMMIT" MODEL_STARTED="$MODEL_STARTED" RUNNER_EXIT="$RUNNER_EXIT" EVAL_EXIT="$EVAL_EXIT" RUNNER_FILE="$RUNNER_FILE" SHELL_EXIT="$shell_exit" START="$START" python3 - <<'PY'
import json,os,time
from pathlib import Path
def env(s): return os.getenv(s,"")
out=Path("v11-public-manual/result.json")
p=Path(env("RUNNER_FILE"))
runner={}
if p.is_file():
    try: runner=json.loads(p.read_text())
    except (ValueError, OSError): pass
identity=(runner.get("model")==os.getenv("MODEL_ID") and runner.get("effort")==os.getenv("REASONING_EFFORT"))
turn_limit=bool(runner.get("turn_limit_reached")) or (runner.get("max_turns") and runner.get("responses",0)>=runner["max_turns"])
shell_limit=bool(runner.get("shell_budget_reached")) or (runner.get("shell_budget") and runner.get("shell_commands",0)>=runner["shell_budget"])
bad=bool(runner.get("infrastructure_error")) or not identity or env("RUNNER_EXIT")!="0" or env("EVAL_EXIT") in ("999","124","137") or env("SHELL_EXIT")!="0"
admissible=not bad and not runner.get("model_timeout") and not (turn_limit or shell_limit or runner.get("cumulative_input_budget_reached"))
result={
 "source":"SWE-bench Multilingual", "task":env("CASE"),"source_commit":env("UPSTREAM_COMMIT"),
 "base_commit":env("BASE"),"model":os.getenv("MODEL_ID"),"effort":os.getenv("REASONING_EFFORT"),
 "score":(100 if env("EVAL_EXIT")=="0" else 0) if admissible else None,
 "classification":("valid-official-pass" if env("EVAL_EXIT")=="0" else "valid-official-fail") if admissible else "incomplete-or-budget-confounded",
 "data_complete":admissible,"runner_telemetry_present":bool(runner),"actual_model":runner.get("model"),
 "actual_effort":runner.get("effort"),"agent_exit_code":int(env("RUNNER_EXIT")),"verifier_exit_code":int(env("EVAL_EXIT")),
 "stage":env("STAGE"),"agent_network":"none","evaluator_network":"bridge",
 "offline_local_test_warmup":env("CASE") in ("google__gson-2158","google__gson-2311","axios__axios-5316","google__gson-1014","google__gson-2134","vuejs__core-11870","vuejs__core-11915","google__gson-1093","vuejs__core-11739"),
 "model_started":env("MODEL_STARTED")=="true",
 "duration_seconds":runner.get("duration_seconds"),
 "total_wall_seconds":int(time.time())-int(env("START")),
 "responses":runner.get("responses",0),"shell_commands":runner.get("shell_commands",0),
 "max_turns":runner.get("max_turns"),"shell_budget":runner.get("shell_budget"),
 "turn_limit_reached":bool(turn_limit),"shell_budget_reached":bool(shell_limit),
 "cumulative_input_budget_reached":bool(runner.get("cumulative_input_budget_reached")),"cumulative_input_token_limit":runner.get("cumulative_input_token_limit"),
 "model_timeout":bool(runner.get("model_timeout")),"infrastructure_error":runner.get("infrastructure_error"),
 "usage":runner.get("usage",{}),
 "note":"Binary official suite evaluation only; one sample is not stable difficulty evidence."
}
out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
PY
  exit "$shell_exit"
}
trap finalize EXIT

read -r CASE BASE UPSTREAM_COMMIT < <(python3 - <<'PY'
import json,os
from pathlib import Path
m=json.loads(Path('benchmarks/v1.1-public-candidates.json').read_text())
case=os.environ['CASE_ID']
allow={
 'google__gson-1014','google__gson-2134','google__gson-1093',
 'google__gson-2158','google__gson-2311','axios__axios-5316',
 'vuejs__core-11589','vuejs__core-11899',
 'vuejs__core-11870','vuejs__core-11915','vuejs__core-11739'}
if case not in allow:raise SystemExit('Unadmitted public case')
row=next((t for t in m['source_candidates'] if t['id']==case),None)
if row is None or row.get('environment_status')!='environment_ready' or row.get('reference_test_status')!='baseline_failed_reference_passed':
    raise SystemExit('No verified official task baseline/reference')
v=row.get('environment_validation') or {}
if v.get('baseline_exit_code') in (0,124,137,999,None) or v.get('reference_exit_code')!=0:
    raise SystemExit('Official reference invalid')
if case in ('google__gson-2158','google__gson-2311','axios__axios-5316'):
    if row.get('offline_agent_warmup_reference_run_id')!=37764439033:raise SystemExit('Not offline-admitted')
elif case in ('google__gson-1014','google__gson-2134','vuejs__core-11870','vuejs__core-11915'):
    if row.get('offline_agent_warmup_reference_run_id')!=37872743296:raise SystemExit('Not offline-admitted')
elif case in ('google__gson-1093','vuejs__core-11739'):
    if row.get('offline_agent_warmup_reference_run_id')!=37875192582:raise SystemExit('Not offline-admitted')
print(case,row['base_commit'],m['dataset_pinned_revision'])
PY
)
STAGE="prepare-task"
mkdir -p "$OUTDIR/agent-work"
UPSTREAM_TASK="https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$UPSTREAM_COMMIT/tasks/$CASE"
curl --retry 2 --fail --silent --show-error --max-time 45 "$UPSTREAM_TASK/problem_statement.md" -o "$OUTDIR/agent-work/TASK.md"
curl --retry 2 --fail --silent --show-error --max-time 45 "$UPSTREAM_TASK/task.yaml" -o "$OUTDIR/upstream-task.yaml"
IMAGE=$(sed -n 's/^image: //p' "$OUTDIR/upstream-task.yaml" | tr -d '\r')
PIN=$(sed -n 's/^base_commit: //p' "$OUTDIR/upstream-task.yaml" | tr -d '\r')
test "$PIN" = "$BASE"
[[ "$IMAGE" == swebench/sweb.eval.x86_64.* ]]
STAGE="pull-official-image"
timeout 180s docker pull "$IMAGE" > "$OUTDIR/pull.log" 2>&1
C="v11-manual-${GITHUB_RUN_ID:-local}"
STAGE="launch-isolated-repo"
AGENT_INITIAL_NETWORK=none
case "$CASE" in
  google__gson-2158|google__gson-2311|axios__axios-5316|google__gson-1014|google__gson-2134|vuejs__core-11870|vuejs__core-11915|google__gson-1093|vuejs__core-11739)
    # Whitelist only tasks that passed source-only offline local-test
    # and official baseline/gold tests in no-model preflight.
    python3 - "$CASE" <<'PY'
import json,sys
from pathlib import Path
case=sys.argv[1]
if case in ("google__gson-1093","vuejs__core-11739"):
    record=json.loads(Path("benchmarks/v1.1-agent-warmup-round3.json").read_text())
    assert record["offline_warmup_run_id"]==37875192582
elif case in ("google__gson-1014","google__gson-2134","vuejs__core-11870","vuejs__core-11915"):
    record=json.loads(Path("benchmarks/v1.1-agent-warmup-round2.json").read_text())
    assert record["offline_warmup_run_id"]==37872743296
else:
    record=json.loads(Path("benchmarks/v1.1-agent-warmup-admission.json").read_text())
    assert record["preflight_run_id"]==37764439033
item=record["task_results"][case]
assert item["status"]=="offline_agent_ready"
assert item["baseline_exit_code"] not in (0,124,137,999)
assert item["reference_exit_code"]==0
PY
    AGENT_INITIAL_NETWORK=bridge
    ;;
esac
docker run -d --name "$C" --network "$AGENT_INITIAL_NETWORK" --cap-drop ALL --security-opt no-new-privileges \
    --memory 4g --cpus 2 "$IMAGE" sleep infinity >/dev/null
docker exec -w /testbed "$C" git reset --hard "$BASE" > "$OUTDIR/reset.log" 2>&1
test "$(docker exec -w /testbed "$C" git rev-parse HEAD | tr -d '\r')" = "$BASE"
if [[ "$AGENT_INITIAL_NETWORK" == bridge ]]; then
  STAGE="pre-model-local-test-warmup"
  AGENT_DOCKER_CONTAINER="$C" BASE_COMMIT="$BASE" CASE_ID="$CASE" \
    WARMUP_LOG_DIR="$OUTDIR/agent-warmup" bash scripts/v11-public-agent-deps.sh
fi
# No LLM request is permitted until this proves the agent has no network.
# Docker's builtin 'none' mode may have a Networks.none entry, while a
# detached bridge container has no entries. Admit only these two exact states.
if [[ "$AGENT_INITIAL_NETWORK" == none ]]; then
  test "$(docker inspect "$C" --format '{{.HostConfig.NetworkMode}}')" = none || {
    echo "Expected Docker --network none, refuse model billing" >&2
    exit 1
  }
else
  test "$(docker inspect "$C" --format '{{len .NetworkSettings.Networks}}')" = 0 || {
    echo "Bridge was not detached, refuse model billing" >&2
    exit 1
  }
fi

STAGE="manual-public-agent"
MODEL_STARTED=true
RUNNER_FILE="$OUTDIR/agent-work/light-agent-result.json"
set +e
AGENT_TASK_PROFILE=public-swe-bench \
AGENT_DOCKER_CONTAINER="$C" AGENT_DOCKER_WORKDIR=/testbed \
AGENT_MAX_TURNS=30 AGENT_SHELL_BUDGET=40 \
AGENT_CAPTURE_SHELL_TRACE=1 AGENT_MAX_OUTPUT_TOKENS=4096 \
AGENT_SHELL_TIMEOUT_MS=90000 AGENT_API_TIMEOUT_MS=140000 \
AGENT_MAX_CUMULATIVE_INPUT_TOKENS=200000 \
AGENT_WALL_TIMEOUT_MS=540000 \
timeout 560s node scripts/light-agent-runner.mjs "$OUTDIR/agent-work" "$MODEL_ID" "$REASONING_EFFORT" "$RUNNER_FILE" > "$OUTDIR/agent.log" 2>&1
RUNNER_EXIT=$?
set -e

# Preserve model patch before running the hidden evaluator, independent of test outcome.
# Preserve tracked AND new source files. Ignored dependency caches stay ignored.
docker exec -w /testbed "$C" git add -N . || true
docker exec -w /testbed "$C" git diff --binary "$BASE" > "$OUTDIR/model.patch" || true
if [[ "$RUNNER_EXIT" != 0 ]]; then
  STAGE="agent-incomplete"
  exit 1
fi

STAGE="prepare-connected-evaluator"
# The no-network agent has finished. Grade its captured diff in a DIFFERENT
# online verifier container so no solution patch or network leaks into the agent.
VC="${C}-verify"
docker run -d --name "$VC" --network bridge --cap-drop ALL --security-opt no-new-privileges \
    --memory 4g --cpus 2 "$IMAGE" sleep infinity >/dev/null
docker exec -w /testbed "$VC" git reset --hard "$BASE" > "$OUTDIR/verifier-reset.log" 2>&1
if [[ -s "$OUTDIR/model.patch" ]]; then
  docker cp "$OUTDIR/model.patch" "$VC:/tmp/model.patch"
  docker exec -w /testbed "$VC" git apply --check /tmp/model.patch
  docker exec -w /testbed "$VC" git apply /tmp/model.patch
fi
STAGE="official-evaluation"
UPSTREAM="https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$UPSTREAM_COMMIT/tasks/$CASE"
for asset in eval.sh; do
  curl --retry 2 --fail --silent --show-error --max-time 45 "$UPSTREAM/$asset" -o "$OUTDIR/$asset"
  docker cp "$OUTDIR/$asset" "$VC:/tmp/v11-eval.sh"
done
set +e
timeout 210s docker exec -w /testbed "$VC" bash -e /tmp/v11-eval.sh > "$OUTDIR/official-eval.log" 2>&1
EVAL_EXIT=$?
set -e
if [[ "$EVAL_EXIT" == 124 || "$EVAL_EXIT" == 137 ]]; then
  STAGE="evaluator-timeout"
  exit 1
fi
STAGE="completed"
