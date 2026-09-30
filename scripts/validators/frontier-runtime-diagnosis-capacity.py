#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); json_mode="--json" in sys.argv[2:]
r={"syntax":False,"root_a":False,"root_b":False,"action_a":False,"action_b":False,"minimal":False}
try:
 x=json.loads((root/"REPAIR.json").read_text()); roots=x.get("root_causes"); actions=x.get("actions")
 if isinstance(roots,list) and isinstance(actions,list) and all(isinstance(v,str) for v in roots+actions):
  r["syntax"]=True
  r["root_a"]="capacity_shortage" in roots
  r["root_b"]="stale_consumer" in roots
  r["action_a"]="scale_api" in actions
  r["action_b"]="upgrade_all_consumers" in actions
  r["minimal"]=set(roots)=={"capacity_shortage","stale_consumer"} and len(roots)==2 and set(actions)=={"scale_api","upgrade_all_consumers"} and len(actions)==2
except Exception: pass
if json_mode: print(json.dumps(r)); raise SystemExit(0)
if not all([r["syntax"],r["root_a"],r["root_b"],r["action_a"],r["action_b"],r["minimal"]]):
 print("VALIDATION_FAIL: repair does not minimally cover proven capacity and fulfillment-retry causes"); raise SystemExit(1)
print("VALIDATION_PASS: capacity and consumer retry causes repaired minimally")
