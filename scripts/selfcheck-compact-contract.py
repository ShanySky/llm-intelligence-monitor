#!/usr/bin/env python3
"""No-model-cost admission check: baseline must fail hidden checks; reference must pass all."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

repo = Path(__file__).resolve().parent.parent
tasks = ("frontier-compact-idempotency", "frontier-compact-outbox", "frontier-compact-lease", "frontier-compact-delivery")
evidence = []
with tempfile.TemporaryDirectory(prefix="compact-reference-") as d:
    for task in tasks:
        base = repo / "benchmarks" / task
        work = Path(d) / task
        shutil.copytree(base / "workspace", work)
        def run(tag):
            result_path = Path(d) / (task + "-" + tag + ".json")
            proc = subprocess.run([sys.executable,
              str(repo / "scripts" / "score-compact-contract.py"), task,
              str(work), str(result_path)], capture_output=True, text=True, timeout=65)
            if proc.returncode:
                raise RuntimeError(proc.stderr or proc.stdout or task + " scorer failed")
            return json.loads(result_path.read_text())
        baseline = run("baseline")
        for original in (base / "reference" / "src").glob("*.java"):
            shutil.copy2(original, work / "src" / original.name)
        reference = run("reference")
        good = (baseline["score"] < 100 and
                baseline["checks"]["compiles"]["passed"] and
                baseline["checks"]["visible_regression"]["passed"] and
                reference["score"] == 100)
        evidence.append({"task": task, "baseline": baseline["score"],
                         "reference": reference["score"], "passed": good})
        if not good:
            print(json.dumps(evidence, indent=2))
            raise SystemExit("Compact candidate reference admission failed: " + task)
report = {"reference_admission": "PASS", "cases": evidence}
(repo / "compact-reference-admission.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
