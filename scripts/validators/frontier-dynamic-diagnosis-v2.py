#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]
m=re.search(r"-t(\d+)(?:$|[^0-9])", root.name)
trial=int(m.group(1)) if m else 1
variant=((trial-1)%3)+1

expected={
  1:({"api_config_drift","retry_idempotency_scope"},{"replace_drifted_api","fix_business_idempotency"}),
  2:({"capacity_shortage","stale_consumer_contract"},{"scale_checkout_api","replace_incompatible_consumer"}),
  3:({"cache_invalidator_gap","replica_read_lag"},{"repair_dual_invalidation","route_strict_reads_primary"}),
}[variant]
known_roots={"api_config_drift","retry_idempotency_scope","stale_consumer_contract","cache_invalidator_gap","capacity_shortage","replica_read_lag"}
known_actions={"replace_drifted_api","fix_business_idempotency","replace_incompatible_consumer","repair_dual_invalidation","scale_checkout_api","route_strict_reads_primary","restart_everything","flush_all_cache","reset_queue","disable_retries"}

out={"variant":variant,"syntax":False,"known_unique":False,"correct_roots":False,"correct_actions":False,"minimal":False}
try:
    x=json.loads((root/"DIAGNOSIS.json").read_text())
    roots=x.get("root_causes"); actions=x.get("actions")
    if isinstance(roots,list) and isinstance(actions,list) and all(isinstance(v,str) for v in roots+actions):
        rs=set(roots); ac=set(actions)
        out["syntax"]=True
        out["known_unique"]=len(rs)==len(roots) and len(ac)==len(actions) and rs<=known_roots and ac<=known_actions
        out["correct_roots"]=rs==expected[0]
        out["correct_actions"]=ac==expected[1]
        out["minimal"]=out["correct_roots"] and out["correct_actions"]
except Exception:
    pass

if json_mode:
    print(json.dumps(out)); raise SystemExit(0)
if not out["syntax"]:
    print("VALIDATION_FAIL format"); raise SystemExit(1)
if not out["known_unique"]:
    print("VALIDATION_FAIL catalog"); raise SystemExit(1)
if not out["correct_roots"]:
    print("VALIDATION_FAIL diagnosis: selected causes do not explain current runtime evidence"); raise SystemExit(1)
if not out["correct_actions"]:
    print("VALIDATION_FAIL repair: selected actions do not minimally repair diagnosed causes"); raise SystemExit(1)
print("VALIDATION_PASS: hidden incident diagnosed and minimally repaired")
