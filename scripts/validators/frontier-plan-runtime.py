#!/usr/bin/env python3
import json
import sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]
decision_path=root/"DECISION.json"

domains={
  "syntax": False,
  "known_unique_actions": False,
  "online_safe": False,
  "persistence_compatibility": False,
  "backfill_race_safety": False,
  "event_compatibility": False,
  "cache_compatibility": False,
  "cutover_gate": False,
  "rollback_safety": False,
  "minimal_sufficient": False,
}

known={
  "expand_schema",
  "deploy_compat_release",
  "enable_guarded_backfill",
  "run_backfill",
  "upgrade_event_consumers",
  "enable_v2_event_producer",
  "enable_dual_namespace_cache",
  "cutover_primary_reads",
  "retire_v1_writers",
  "close_rollback_window",
  "cleanup_legacy_contracts",
  "pause_all_writes",
  "flush_entire_cache",
  "restart_all_services",
}
required={
  "expand_schema",
  "deploy_compat_release",
  "enable_guarded_backfill",
  "run_backfill",
  "upgrade_event_consumers",
  "enable_v2_event_producer",
  "enable_dual_namespace_cache",
  "cutover_primary_reads",
  "retire_v1_writers",
  "close_rollback_window",
  "cleanup_legacy_contracts",
}
dangerous={"pause_all_writes","flush_entire_cache","restart_all_services"}

steps=[]
error=None
try:
    raw=json.loads(decision_path.read_text())
    if isinstance(raw,dict) and isinstance(raw.get("steps"),list) and all(isinstance(x,str) for x in raw["steps"]):
        steps=raw["steps"]
        domains["syntax"]=True
    else:
        error="DECISION.json must contain a string array named steps"
except Exception as exc:
    error=f"invalid DECISION.json: {exc}"

if domains["syntax"]:
    domains["known_unique_actions"]=all(x in known for x in steps) and len(set(steps))==len(steps)

def pos(name):
    try: return steps.index(name)
    except ValueError: return None

if domains["known_unique_actions"]:
    domains["online_safe"]=not any(x in dangerous for x in steps)

    ex=pos("expand_schema")
    compat=pos("deploy_compat_release")
    guard=pos("enable_guarded_backfill")
    backfill=pos("run_backfill")
    consumers=pos("upgrade_event_consumers")
    producer=pos("enable_v2_event_producer")
    cache=pos("enable_dual_namespace_cache")
    cutover=pos("cutover_primary_reads")
    retire=pos("retire_v1_writers")
    close=pos("close_rollback_window")
    cleanup=pos("cleanup_legacy_contracts")

    domains["persistence_compatibility"]=(
        ex is not None and compat is not None and ex < compat
        and retire is not None and compat < retire
    )
    domains["backfill_race_safety"]=(
        compat is not None and guard is not None and backfill is not None
        and compat < guard < backfill
    )
    domains["event_compatibility"]=(
        consumers is not None and producer is not None
        and consumers < producer
    )
    domains["cache_compatibility"]=(
        compat is not None and cache is not None and cutover is not None
        and compat < cache < cutover
    )
    domains["cutover_gate"]=(
        backfill is not None and producer is not None and cache is not None
        and cutover is not None
        and backfill < cutover and producer < cutover and cache < cutover
    )
    domains["rollback_safety"]=(
        compat is not None and retire is not None and close is not None and cleanup is not None
        and compat < retire < close < cleanup
    )
    domains["minimal_sufficient"]=(
        set(steps)==required and len(steps)==len(required)
    )

result={"domains":domains,"steps":steps,"error":error}

if json_mode:
    print(json.dumps(result))
    raise SystemExit(0)

if not domains["syntax"]:
    print("VALIDATION_FAIL format: rollout decision is not parseable")
    raise SystemExit(1)
if not domains["known_unique_actions"]:
    print("VALIDATION_FAIL action-set: rollout contains an unknown or repeated action")
    raise SystemExit(1)
if not domains["online_safe"]:
    print("VALIDATION_FAIL availability: the rollout relies on a broad disruptive action instead of preserving online compatibility")
    raise SystemExit(1)
if not domains["persistence_compatibility"]:
    print("VALIDATION_FAIL mixed-db: mixed-version persistence or rollback becomes unsafe during the sequence")
    raise SystemExit(1)
if not domains["backfill_race_safety"]:
    print("VALIDATION_FAIL backfill-race: live traffic can be overwritten by migration work")
    raise SystemExit(1)
if not domains["event_compatibility"]:
    print("VALIDATION_FAIL event-contract: some rolling consumer state cannot safely process produced events")
    raise SystemExit(1)
if not domains["cache_compatibility"]:
    print("VALIDATION_FAIL cache-contract: mixed-version writes can produce stale or missing reads around cutover")
    raise SystemExit(1)
if not domains["cutover_gate"]:
    print("VALIDATION_FAIL cutover-gate: primary reads switch before all required compatibility domains are ready")
    raise SystemExit(1)
if not domains["rollback_safety"]:
    print("VALIDATION_FAIL rollback: irreversible compatibility cleanup occurs before rollback is safely closed")
    raise SystemExit(1)
if not domains["minimal_sufficient"]:
    print("VALIDATION_FAIL minimality: the plan is not the minimal complete set of rollout actions")
    raise SystemExit(1)

print("VALIDATION_PASS: mixed-version, live migration, event, cache, cutover, rollback, and minimality checks passed")
