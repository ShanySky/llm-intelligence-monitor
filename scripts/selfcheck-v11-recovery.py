#!/usr/bin/env python3
"""No-model-cost selfcheck: baseline visible PASS / hidden partial; reference hidden 100."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
repo=Path(__file__).resolve().parent.parent
results=[]
with tempfile.TemporaryDirectory(prefix="v11-reference-") as td:
    for variant in ("payment","lease","identity"):
        source=repo/"benchmarks"/"v11-recovery"/"instances"/variant
        ws=Path(td)/variant
        shutil.copytree(source/"workspace",ws)
        def score(stage):
            out=Path(td)/(variant+"-"+stage+".json")
            subprocess.run([sys.executable,str(repo/"scripts"/"score-v11-recovery.py"),
                            "v11-recovery-"+variant,str(ws),str(out)],check=True,capture_output=True,text=True,timeout=50)
            return json.loads(out.read_text())
        before=score("baseline")
        for f in (source/"reference"/"src").glob("*.py"):
            shutil.copy2(f,ws/"src"/f.name)
        after=score("reference")
        passed=20<=before["score"]<=80 and after["score"]==100 and before["checks"]["visible_regression"]["passed"] and after["checks"]["visible_regression"]["passed"]
        results.append({"variant":variant,"baseline":before["score"],"reference":after["score"],"passed":passed})
        if not passed: raise SystemExit("Reference admission failed: "+json.dumps(results))
report={"reference_admission":"PASS","cases":results}
(repo/"v11-reference-admission.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
