#!/usr/bin/env python3
"""No-API regression for causal evidence scoring.

A query string alone, or an observational (non-intervention) response, must not
earn the experimental-evidence points. Legitimate probe outputs must earn them.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CASES = {
    "frontier-runtime-diagnosis-capacity": {
        "roots": ["capacity_shortage", "stale_consumer"],
        "actions": ["scale_api", "upgrade_all_consumers"],
        "generic": ["capacity load", "consumer revisions"],
        "causal": ["controlled capacity replica experiment", "controlled delivery replay experiment"],
    },
    "frontier-runtime-diagnosis-cache-db": {
        "roots": ["cache_invalidator_mismatch", "database_pool_exhaustion"],
        "actions": ["replace_all_invalidators", "increase_db_pool"],
        "generic": ["cache invalidator state", "database pool waiters"],
        "causal": ["controlled invalidator cache experiment", "controlled database pool experiment"],
    },
}

def run_probe(name, root, query):
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "probes" / (name + ".py")),
         str(root), query], text=True, capture_output=True, timeout=5)
    assert proc.returncode == 0, (name, query, proc.stderr)
    return {"query": query, "output": proc.stdout.strip(), "exit_code": 0}

def scored(name, root, observations, query_only=False):
    trace = {
        "probe_calls": len(observations),
        "probe_executed_queries": [x["query"] for x in observations],
        "probe_observations": [] if query_only else observations,
    }
    (root / "light-agent-result.json").write_text(json.dumps(trace))
    score_file = root / "score.json"
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "score-application-task.py"),
         name, str(root), str(score_file)],
        text=True, capture_output=True, timeout=20)
    assert proc.returncode == 0, (name, proc.stderr, proc.stdout)
    return json.loads(score_file.read_text())

with tempfile.TemporaryDirectory(prefix="causal-evidence-test-") as td:
    for name, spec in CASES.items():
        root = Path(td) / name
        root.mkdir()
        (root / "REPAIR.json").write_text(json.dumps({
            "root_causes": spec["roots"], "actions": spec["actions"]}))
        generic = [run_probe(name, root, q) for q in spec["generic"]]
        causal = [run_probe(name, root, q) for q in spec["causal"]]
        query_only = scored(name, root, causal, query_only=True)
        observed = scored(name, root, generic)
        actual = scored(name, root, causal)
        failed_probes = scored(name, root, [{**o, "exit_code": 1} for o in causal])
        assert query_only["score"] == 85, (name, "query only", query_only)
        assert observed["score"] == 85, (name, "generic observations", observed)
        assert failed_probes["score"] == 85, (name, "failed probe", failed_probes)
        assert actual["score"] == 100, (name, "experiment", actual)
        print(f"PASS {name}: query/observation/failure=85, causal-interventions=100")

print("PASS runtime causal evidence scoring regression")
