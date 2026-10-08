#!/usr/bin/env python3
"""Objective hidden Java checks for compact cross-file contract micro-repositories.

Hidden verifier sources remain outside the model-visible /workspace tree.
The only input from the model is the modified working tree passed as root.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

task = sys.argv[1]
root = Path(sys.argv[2]).resolve()
out = Path(sys.argv[3]).resolve()
tasks = {
    "frontier-compact-idempotency": ("TENANT", "REVISION", "TOPIC", "PARALLEL"),
    "frontier-compact-outbox": ("DURABLE", "ACK_WINDOW", "REPEAT", "UNRELATED"),
    "frontier-compact-lease": ("STALE", "DEADLINE", "RENEW", "SEPARATE"),
}
if task not in tasks:
    raise SystemExit("unknown compact task " + task)

repo = Path(__file__).resolve().parent.parent
hidden_file = repo / "benchmarks" / task / "hidden" / "HiddenVerifier.java"
checks = {}
score = 0

def add(name, weight, passed):
    global score
    passed = bool(passed)
    checks[name] = {"points": weight, "passed": passed}
    if passed:
        score += weight

sources = sorted((root / "src").glob("*.java"))
with tempfile.TemporaryDirectory(prefix="compact-hidden-") as td:
    target = Path(td)
    compiled = False
    visible_ok = False
    hidden_output = ""
    if sources and hidden_file.is_file():
        cp = subprocess.run(["javac", "-encoding", "UTF-8", "-d", str(target),
                             *map(str, sources), str(hidden_file)],
                            capture_output=True, text=True, timeout=25)
        compiled = cp.returncode == 0
        if compiled:
            visible = subprocess.run(["java", "-cp", str(target), "VisibleTest"],
                                     capture_output=True, text=True, timeout=15)
            visible_ok = visible.returncode == 0 and "VISIBLE_PASS" in visible.stdout
            hidden = subprocess.run(["java", "-cp", str(target), "HiddenVerifier"],
                                    capture_output=True, text=True, timeout=20)
            hidden_output = hidden.stdout
    add("compiles", 10, compiled)
    add("visible_regression", 10, visible_ok)
    weights = [20, 20, 20, 20]
    for name, weight in zip(tasks[task], weights):
        add(name.lower(), weight, name + "_PASS" in hidden_output.splitlines())

# Only production code is editable. A candidate that changes the task, contracts,
# visible regression tests, or run script cannot receive behavioral credit.
protected = ["TASK.md", "src/VisibleTest.java", "run_visible_tests.sh"]
protected += [str(p.relative_to(repo / "benchmarks" / task / "workspace"))
              for p in (repo / "benchmarks" / task / "workspace" / "contracts").rglob("*")
              if p.is_file()]
changed_protected = [rel for rel in protected if
    not (root / rel).is_file() or
    (root / rel).read_bytes() !=
    (repo / "benchmarks" / task / "workspace" / rel).read_bytes()]
add("preserves_protected_contracts", 0, not changed_protected)
if changed_protected:
    score = 0
result = {"task": task, "score": score, "checks": checks,
          "protected_changes": changed_protected,
          "verifier": "compact-contract-hidden-v2"}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
