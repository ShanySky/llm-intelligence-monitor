#!/usr/bin/env python3
import json, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]
path=root/"REPAIR.json"

result={
  "syntax":False,
  "root_causes":[],
  "actions":[],
  "config_root":False,
  "idempotency_root":False,
  "config_action":False,
  "idempotency_action":False,
  "minimal":False,
}

try:
    data=json.loads(path.read_text())
    roots=data.get("root_causes")
    actions=data.get("actions")
    if isinstance(roots,list) and isinstance(actions,list) and all(isinstance(x,str) for x in roots+actions):
        result["syntax"]=True
        result["root_causes"]=roots
        result["actions"]=actions
        result["config_root"]="api_config_drift" in roots
        result["idempotency_root"]="retry_idempotency_scope" in roots
        result["config_action"]="replace_drifted_api_from_desired" in actions
        result["idempotency_action"]="use_order_version_idempotency" in actions
        result["minimal"]=(
            set(roots)=={"api_config_drift","retry_idempotency_scope"}
            and len(roots)==2
            and set(actions)=={"replace_drifted_api_from_desired","use_order_version_idempotency"}
            and len(actions)==2
        )
except Exception:
    pass

if json_mode:
    print(json.dumps(result))
    raise SystemExit(0)

if not result["syntax"]:
    print("VALIDATION_FAIL format: REPAIR.json is invalid")
    raise SystemExit(1)
if not result["config_root"]:
    print("VALIDATION_FAIL http-errors: the repair does not explain the pod-specific 500s")
    raise SystemExit(1)
if not result["idempotency_root"]:
    print("VALIDATION_FAIL retry-effects: the repair does not explain duplicate provider effects on a healthy API pod")
    raise SystemExit(1)
if not result["config_action"]:
    print("VALIDATION_FAIL config-repair: the proven drift is not repaired")
    raise SystemExit(1)
if not result["idempotency_action"]:
    print("VALIDATION_FAIL retry-repair: timeout retries can still create multiple business effects")
    raise SystemExit(1)
if not result["minimal"]:
    print("VALIDATION_FAIL minimality: the repair includes unrelated or redundant causes/actions")
    raise SystemExit(1)

print("VALIDATION_PASS: both causal domains are repaired without unrelated rollout changes")
