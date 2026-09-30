#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]
m=re.search(r"-t(\d+)(?:$|[^0-9])", root.name)
trial=int(m.group(1)) if m else 1
variant=((trial-1)%3)+1

expected={
  1:{
    "roots":{"api_config_drift","retry_idempotency_scope"},
    "actions":{"replace_drifted_api","fix_business_idempotency"},
  },
  2:{
    "roots":{"capacity_shortage","stale_consumer_contract"},
    "actions":{"scale_checkout_api","replace_incompatible_consumer"},
  },
  3:{
    "roots":{"cache_invalidator_gap","replica_read_lag"},
    "actions":{"repair_dual_invalidation","route_strict_reads_primary"},
  },
}[variant]

known_roots={
 "api_config_drift","retry_idempotency_scope","stale_consumer_contract",
 "cache_invalidator_gap","capacity_shortage","replica_read_lag"
}
known_actions={
 "replace_drifted_api","fix_business_idempotency","replace_incompatible_consumer",
 "repair_dual_invalidation","scale_checkout_api","route_strict_reads_primary",
 "restart_everything","flush_all_cache","reset_queue","disable_retries"
}

result={
 "variant":variant,"syntax":False,"known_unique":False,
 "correct_roots":False,"correct_actions":False,"minimal":False,
 "root_precision":0.0,"root_recall":0.0,"action_precision":0.0,"action_recall":0.0,
}
try:
    data=json.loads((root/"DIAGNOSIS.json").read_text())
    roots=data.get("root_causes"); actions=data.get("actions")
    if isinstance(roots,list) and isinstance(actions,list) and all(isinstance(x,str) for x in roots+actions):
        result["syntax"]=True
        roots_set=set(roots); actions_set=set(actions)
        result["known_unique"]=(
            len(roots_set)==len(roots) and len(actions_set)==len(actions)
            and roots_set<=known_roots and actions_set<=known_actions
        )
        result["correct_roots"]=roots_set==expected["roots"]
        result["correct_actions"]=actions_set==expected["actions"]
        result["minimal"]=result["correct_roots"] and result["correct_actions"]
        if roots_set:
            result["root_precision"]=len(roots_set & expected["roots"])/len(roots_set)
        result["root_recall"]=len(roots_set & expected["roots"])/len(expected["roots"])
        if actions_set:
            result["action_precision"]=len(actions_set & expected["actions"])/len(actions_set)
        result["action_recall"]=len(actions_set & expected["actions"])/len(expected["actions"])
except Exception:
    pass

if json_mode:
    print(json.dumps(result)); raise SystemExit(0)

if not result["syntax"]:
    print("VALIDATION_FAIL format: DIAGNOSIS.json is invalid"); raise SystemExit(1)
if not result["known_unique"]:
    print("VALIDATION_FAIL catalog: unknown or repeated IDs"); raise SystemExit(1)
if not result["correct_roots"]:
    print("VALIDATION_FAIL diagnosis: selected failure domains do not explain the current runtime evidence"); raise SystemExit(1)
if not result["correct_actions"]:
    print("VALIDATION_FAIL repair: selected actions do not minimally repair the diagnosed domains"); raise SystemExit(1)
print("VALIDATION_PASS: current hidden incident is correctly diagnosed and minimally repaired")
