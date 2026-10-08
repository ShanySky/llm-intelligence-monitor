#!/usr/bin/env python3
"""Objective hidden behavior scoring; tests remain outside the model workspace."""
import json,subprocess,sys
from pathlib import Path
task,workspace,out=sys.argv[1],Path(sys.argv[2]).resolve(),Path(sys.argv[3]).resolve()
labels={"v11-recovery-payment":["REPLAY","CRASH","SCOPE","GUARD"],
        "v11-recovery-lease":["RACE","EXPIRE","RETRY","ISOLATE"],
        "v11-recovery-identity":["LEGACY","V2","STALE","TENANT"]}
if task not in labels: raise SystemExit("unknown task "+task)
variant=task[len("v11-recovery-"):]
repo=Path(__file__).resolve().parent.parent
src=repo/"benchmarks"/"v11-recovery"/"instances"/variant/"workspace"
protected=["TASK.md","run_visible_tests.sh","src/visible_test.py"]
protected += [str(p.relative_to(src)) for p in (src/"contracts").rglob("*") if p.is_file()]
changed=[p for p in protected if not (workspace/p).exists() or (workspace/p).read_bytes() != (src/p).read_bytes()]
visible=subprocess.run([sys.executable,str(workspace/"src"/"visible_test.py")],cwd=workspace,capture_output=True,text=True,timeout=15)
hidden=subprocess.run([sys.executable,str(repo/"benchmarks"/"v11-recovery"/"hidden"/"verify.py"),variant,str(workspace)],cwd=workspace,capture_output=True,text=True,timeout=20)
seen=set(hidden.stdout.splitlines())
checks={"visible_regression":{"points":20,"passed":visible.returncode==0 and "VISIBLE_PASS" in visible.stdout}}
for name in labels[task]:
    checks[name.lower()]={"points":20,"passed":name+"_PASS" in seen}
checks["protected_contracts"]={"points":0,"passed":not changed}
score=sum(c["points"] for c in checks.values() if c["passed"]) if not changed else 0
result={"task":task,"score":score,"checks":checks,"protected_changes":changed,"verifier":"v11-recovery-hidden-v1",
        "hidden_stderr":hidden.stderr[-500:] if hidden.returncode else None}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
