#!/usr/bin/env bash
set -euo pipefail

# Prepare dependencies in the ORIGINAL project checkout, before giving the agent
# access. The model must never see the upstream test.patch or gold.patch.
CASE_ID="${CASE_ID:?CASE_ID is required}"
C="${AGENT_DOCKER_CONTAINER:?AGENT_DOCKER_CONTAINER is required}"
BASE="${BASE_COMMIT:?BASE_COMMIT is required}"
LOG_DIR="${WARMUP_LOG_DIR:-v11-agent-warmup}"
mkdir -p "$LOG_DIR"
docker exec -w /testbed "$C" git diff --quiet "$BASE" -- || {
  echo "Warmup must start on pristine source" >&2
  exit 1
}
docker inspect "$C" --format '{{json .NetworkSettings.Networks}}' > "$LOG_DIR/networks-before.json"
grep -q '"bridge"' "$LOG_DIR/networks-before.json" || {
  echo "Container must initially be attached to bridge for dependency warmup" >&2
  exit 1
}

case "$CASE_ID" in
 google__gson-1014)
   cmd='mvnd test -B -T 1C -pl gson -Dtest=com.google.gson.stream.JsonReaderTest#testReadArray'
   smoke='mvnd -o test -B -T 1C -pl gson -Dtest=com.google.gson.stream.JsonReaderTest#testReadArray'
   ;;
 google__gson-2134)
   cmd='mvnd test -B -T 1C -pl gson -Dtest=com.google.gson.internal.bind.util.ISO8601UtilsTest#testDateFormatString'
   smoke='mvnd -o test -B -T 1C -pl gson -Dtest=com.google.gson.internal.bind.util.ISO8601UtilsTest#testDateFormatString'
   ;;
 vuejs__core-11870)
   cmd='pnpm run test packages/runtime-core/__tests__/helpers/renderList.spec.ts --no-watch --reporter=verbose'
   smoke='pnpm run test packages/runtime-core/__tests__/helpers/renderList.spec.ts --no-watch --reporter=verbose'
   ;;
 vuejs__core-11915)
   cmd='pnpm run test packages/compiler-core/__tests__/parse.spec.ts --no-watch --reporter=verbose -t "Element"'
   smoke='pnpm run test packages/compiler-core/__tests__/parse.spec.ts --no-watch --reporter=verbose -t "Element"'
   ;;
 google__gson-2158)
   cmd='mvnd test -B -T 1C -pl gson -Dtest=com.google.gson.functional.PrimitiveTest#testByteSerialization'
   smoke='mvnd -o test -B -T 1C -pl gson -Dtest=com.google.gson.functional.PrimitiveTest#testByteSerialization'
   ;;
 google__gson-2311)
   cmd='mvnd test -B -T 1C -pl gson -Dtest=com.google.gson.JsonPrimitiveTest#testLongEqualsBigInteger'
   smoke='mvnd -o test -B -T 1C -pl gson -Dtest=com.google.gson.JsonPrimitiveTest#testLongEqualsBigInteger'
   ;;
 axios__axios-5316)
   # No original tests or model source are modified. Preserve source manifest/lockfile.
   cmd='npm install --no-audit --no-fund && npm install --no-save --package-lock=false --no-audit --no-fund formdata-node@5.0.1 && node -e '\''import("formdata-node").then(m=>{if(!m.FormData||!m.Blob||!m.File)process.exit(1)})'\'''
   smoke='node -e '\''import("formdata-node").then(m=>{if(!m.FormData||!m.Blob||!m.File)process.exit(1)})'\'' && ./node_modules/.bin/mocha test/unit/adapters/http.js -R tap -g "FormData"'
   ;;
 *)
   echo "Warmup not configured for $CASE_ID; don't invent dependency preparation" >&2
   exit 1
   ;;
esac
echo "Prewarming existing codebase and test tooling for $CASE_ID without benchmark test patches"
timeout 220s docker exec -w /testbed "$C" bash -lc "$cmd" > "$LOG_DIR/warm-online.log" 2>&1 || {
  tail -n 55 "$LOG_DIR/warm-online.log" >&2
  echo "Connected dependency warmup failed" >&2
  exit 1
}
# Reinstalling dependencies must not modify the benchmark candidate's source.
docker exec -w /testbed "$C" git diff --exit-code "$BASE" > "$LOG_DIR/prewarm-diff.txt" || {
  echo "Dependency warmup changed tracked source; reject contamination" >&2
  exit 1
}
docker network disconnect bridge "$C"
docker inspect "$C" --format '{{json .NetworkSettings.Networks}}' > "$LOG_DIR/networks-after.json"
test "$(docker inspect "$C" --format '{{len .NetworkSettings.Networks}}')" = 0 || {
  echo "Agent container still has an attached network; abort before model access" >&2
  exit 1
}
# Run an ordinary *existing* test from the unmodified project, without
# loading official hidden/added test patches, while still offline.
timeout 150s docker exec -w /testbed "$C" bash -lc "$smoke" > "$LOG_DIR/test-offline.log" 2>&1 || {
  tail -n 55 "$LOG_DIR/test-offline.log" >&2
  echo "Local tests are NOT offline-ready; do not bill for any model" >&2
  exit 1
}
docker exec -w /testbed "$C" git diff --exit-code "$BASE" > "$LOG_DIR/after-offline-diff.txt" || {
  echo "Offline validation mutated source files" >&2
  exit 1
}
printf '%s\n' "$CASE_ID offline dependency warmup and local test PASS" > "$LOG_DIR/READY"
