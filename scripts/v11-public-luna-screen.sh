#!/usr/bin/env bash
set -euo pipefail

# Official-source screening: only a preflight-admitted task, and only Luna High.
OUTDIR="v11-public-luna"
mkdir -p "$OUTDIR"
STAGE="admission"
START=$(date +%s)
CASE=""
BASE=""
IMAGE=""
UPSTREAM_COMMIT=""
C=""
MODEL_STARTED=false
RUNNER_EXIT=999
EVAL_EXIT=999
RUNNER_FILE=""
AGENT_WALL=540
RESULT_STATUS="incomplete_environment"

finalize() {
  local shell_exit=$?
  if [[ -n "$C" ]]; then docker rm -f "$C" >/dev/null 2>&1 || true; fi
  STAGE="$STAGE" CASE="$CASE" BASE="$BASE" IMAGE="$IMAGE" UPSTREAM_COMMIT="$UPSTREAM_COMMIT" MODEL_STARTED="$MODEL_STARTED" RUNNER_EXIT="$RUNNER_EXIT" EVAL_EXIT="$EVAL_EXIT" RUNNER_FILE="$RUNNER_FILE" SHELL_EXIT="$shell_exit" START="$START" python3 - <<'PY'
import json,os,time
from pathlib import Path
def env(s): return os.getenv(s,"")
out=Path("v11-public-luna/result.json")
p=Path(env("RUNNER_FILE"))
runner={}
if p.is_file():
    try: runner=json.loads(p.read_text())
    except (ValueError, OSError): pass
identity=(runner.get("model")=="gpt-6-luna" and runner.get("effort")=="high")
turn_limit=bool(runner.get("turn_limit_reached")) or (runner.get("max_turns") and runner.get("responses",0)>=runner["max_turns"])
shell_limit=bool(runner.get("shell_budget_reached")) or (runner.get("shell_budget") and runner.get("shell_commands",0)>=runner["shell_budget"])
bad=bool(runner.get("infrastructure_error")) or not identity or env("RUNNER_EXIT")!="0" or env("EVAL_EXIT") in ("999","124","137") or env("SHELL_EXIT")!="0"
admissible=not bad and not runner.get("model_timeout") and not (turn_limit or shell_limit)
result={
 "source":"SWE-bench Multilingual", "task":env("CASE"),"source_commit":env("UPSTREAM_COMMIT"),
 "base_commit":env("BASE"),"model":"gpt-6-luna","effort":"high",
 "score":(100 if env("EVAL_EXIT")=="0" else 0) if admissible else None,
 "classification":("valid-official-pass" if env("EVAL_EXIT")=="0" else "valid-official-fail") if admissible else "incomplete-or-budget-confounded",
 "data_complete":admissible,"runner_telemetry_present":bool(runner),"actual_model":runner.get("model"),
 "actual_effort":runner.get("effort"),"agent_exit_code":int(env("RUNNER_EXIT")),"verifier_exit_code":int(env("EVAL_EXIT")),
 "stage":env("STAGE"),"model_started":env("MODEL_STARTED")=="true",
 "duration_seconds":runner.get("duration_seconds"),
 "total_wall_seconds":int(time.time())-int(env("START")),
 "responses":runner.get("responses",0),"shell_commands":runner.get("shell_commands",0),
 "max_turns":runner.get("max_turns"),"shell_budget":runner.get("shell_budget"),
 "turn_limit_reached":bool(turn_limit),"shell_budget_reached":bool(shell_limit),
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

read -r CASE BASE IMAGE UPSTREAM_COMMIT < <(python3 - <<'PY'
import json
from pathlib import Path
config=json.loads(Path("benchmarks/v1.1-luna-pilot.json").read_text())
manifest=json.loads(Path("benchmarks/v1.1-public-candidates.json").read_text())
if not config["enabled"] or config["model"]!="gpt-6-luna" or config["effort"]!="high":
    raise SystemExit("No Luna-only admission")
task=next((x for x in manifest["source_candidates"] if x["id"]==config["task"]),None)
if task is None or task["environment_status"]!="environment_ready" or task.get("reference_test_status")!="baseline_failed_reference_passed":
    raise SystemExit("Official environment/reference not verified for this task")
if task["environment_validation"]["reference_exit_code"]!=0 or task["environment_validation"]["baseline_exit_code"]==0:
    raise SystemExit("Invalid historical reference admission")
print(task["id"],task["base_commit"],"swebench/sweb.eval.x86_64.google_1776_gson-2158:latest",config["pinned_task_commit"])
PY
)
test "$CASE" = "google__gson-2158"
STAGE="prepare-task"
mkdir -p "$OUTDIR/agent-work"
curl --retry 2 --fail --silent --show-error --max-time 45 \
 "https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$UPSTREAM_COMMIT/tasks/$CASE/problem_statement.md" \
 -o "$OUTDIR/agent-work/TASK.md"

STAGE="pull-official-image"
timeout 180s docker pull "$IMAGE" > "$OUTDIR/pull.log" 2>&1
C="v11-luna-${GITHUB_RUN_ID:-local}"
STAGE="launch-isolated-repo"
docker run -d --name "$C" --network none --cap-drop ALL --security-opt no-new-privileges \
    --memory 4g --cpus 2 "$IMAGE" sleep infinity >/dev/null
docker exec -w /testbed "$C" git reset --hard "$BASE" > "$OUTDIR/reset.log" 2>&1
test "$(docker exec -w /testbed "$C" git rev-parse HEAD | tr -d '\r')" = "$BASE"

STAGE="luna-agent"
MODEL_STARTED=true
RUNNER_FILE="$OUTDIR/agent-work/light-agent-result.json"
set +e
AGENT_TASK_PROFILE=public-swe-bench \
AGENT_DOCKER_CONTAINER="$C" AGENT_DOCKER_WORKDIR=/testbed \
AGENT_MAX_TURNS=30 AGENT_SHELL_BUDGET=40 \
AGENT_CAPTURE_SHELL_TRACE=1 AGENT_MAX_OUTPUT_TOKENS=4096 \
AGENT_SHELL_TIMEOUT_MS=90000 AGENT_API_TIMEOUT_MS=140000 \
AGENT_WALL_TIMEOUT_MS=540000 \
timeout 560s node scripts/light-agent-runner.mjs "$OUTDIR/agent-work" gpt-6-luna high "$RUNNER_FILE" > "$OUTDIR/agent.log" 2>&1
RUNNER_EXIT=$?
set -e

# Preserve model patch before running the hidden evaluator, independent of test outcome.
docker exec -w /testbed "$C" git diff --binary "$BASE" > "$OUTDIR/model.patch" || true
if [[ "$RUNNER_EXIT" != 0 ]]; then
  STAGE="agent-incomplete"
  exit 1
fi

STAGE="official-evaluation"
UPSTREAM="https://raw.githubusercontent.com/SWE-bench/swe-bench-multilingual-tasks/$UPSTREAM_COMMIT/tasks/$CASE"
for asset in eval.sh; do
  curl --retry 2 --fail --silent --show-error --max-time 45 "$UPSTREAM/$asset" -o "$OUTDIR/$asset"
  docker cp "$OUTDIR/$asset" "$C:/tmp/v11-eval.sh"
done
set +e
timeout 210s docker exec -w /testbed "$C" bash -e /tmp/v11-eval.sh > "$OUTDIR/official-eval.log" 2>&1
EVAL_EXIT=$?
set -e
if [[ "$EVAL_EXIT" == 124 || "$EVAL_EXIT" == 137 ]]; then
  STAGE="evaluator-timeout"
  exit 1
fi
STAGE="completed"
