#!/usr/bin/env python3
import json, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]
path=root/"REPAIR.json"
result={
  "syntax":False,
  "config_root":False,
  "retry_root":False,
  "config_action":False,
  "retry_action":False,
  "minimal":False
}
try:
    x=json.loads(path.read_text())
    roots=x.get("root_causes")
    actions=x.get("actions")
    if isinstance(roots,list) and isinstance(actions,list) and all(isinstance(v,str) for v in roots+actions):
        result["syntax"]=True
        result["config_root"]="api_config_drift" in roots
        result["retry_root"]="retry_idempotency_scope" in roots
        result["config_action"]="replace_drifted_api_from_desired" in actions
        result["retry_action"]="use_order_version_idempotency" in actions
        result["minimal"]=(
          roots.count("api_config_drift")==1 and
          roots.count("retry_idempotency_scope")==1 and
          len(roots)==2 and
          actions.count("replace_drifted_api_from_desired")==1 and
          actions.count("use_order_version_idempotency")==1 and
          len(actions)==2
        )
except Exception:
    pass

if json_mode:
    print(json.dumps(result))
    raise SystemExit(0)

if not result["syntax"]:
    print("VALIDATION_FAIL format")
    raise SystemExit(1)
if not result["config_root"]:
    print("VALIDATION_FAIL http-path: pod-specific 500 cause remains unexplained")
    raise SystemExit(1)
if not result["retry_root"]:
    print("VALIDATION_FAIL retry-path: duplicate provider effects remain unexplained")
    raise SystemExit(1)
if not result["config_action"] or not result["retry_action"]:
    print("VALIDATION_FAIL repair: one proven causal domain remains unrepaired")
    raise SystemExit(1)
if not result["minimal"]:
    print("VALIDATION_FAIL minimality: unrelated hypotheses or repairs are included")
    raise SystemExit(1)
print("VALIDATION_PASS: minimal causal repair covers both independent incident domains")
