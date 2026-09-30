#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

root=Path(sys.argv[1]).resolve()
scorer=Path(__file__).resolve().parents[1]/"score-application-task.py"
with tempfile.TemporaryDirectory(prefix="runtime-repair-validator-") as td:
    out=Path(td)/"score.json"
    p=subprocess.run(
        ["python",str(scorer),"frontier-runtime-repair-family",str(root),str(out)],
        capture_output=True,text=True,timeout=45
    )
    if p.returncode != 0 or not out.exists():
        print("VALIDATION_ERROR: hidden validation could not execute")
        raise SystemExit(2)
    result=json.loads(out.read_text())
    score=float(result.get("score",0))
    if score >= 100:
        print("VALIDATION_PASS: runtime incident repair passes hidden behavioral checks")
        raise SystemExit(0)
    if score >= 70:
        print(f"VALIDATION_FAIL: repair is partially correct ({score:.0f}/100); at least one production failure window remains")
    else:
        print(f"VALIDATION_FAIL: repair is incomplete ({score:.0f}/100); core incident behavior still fails")
    raise SystemExit(1)
