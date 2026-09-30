#!/usr/bin/env python3
import sys
q=" ".join(sys.argv[2:]).strip().lower()
if not q or q in {"help","?","commands"} or "everything" in q or "show all" in q:
    print("PROBE_GUIDANCE: ask one focused question about a stale-read path, invalidation, database pool, or another causal hypothesis.")
elif any(x in q for x in ["status","overview","symptom","health"]):
    print("sample: 31 stale read-after-write failures/10000 legacy writes; 17/500 checkout requests timed out waiting for DB connection; provider duplicates=0; API CPU normal")
elif any(x in q for x in ["cache","stale","read-after-write","invalidation","invalidator"]):
    print("mixed invalidators: invalidator-a rev=12 emits numeric+stable-key invalidations; invalidator-b rev=11 emits numeric-only. Stale failures occur only when legacy write is handled by invalidator-b and v2 cache alias already exists")
elif any(x in q for x in ["database","db","pool","connection","waiter","timeout"]):
    print("DB pool: 100% utilized, 37 waiters, acquisition p95=2.4s; query execution p95=18ms; controlled pool increase removes acquisition timeouts without changing query latency")
elif any(x in q for x in ["capacity","cpu","scale","replica"]):
    print("API CPU max=34%, request queue=0; scaling API alone does not change DB acquisition waits")
elif any(x in q for x in ["consumer","event","fulfillment"]):
    print("consumer fleet accepts current schema and retry dedupe checks pass")
elif any(x in q for x in ["provider","payment","idempot"]):
    print("provider retries use stable business key; duplicate effects=0")
elif any(x in q for x in ["config","api-a","api-b","rendered"]):
    print("API rendered configs match desired release; no pod-specific 500 signature")
elif any(x in q for x in ["network","dns","connectivity"]):
    print("network/DNS healthy; database timeout begins after connection acquisition wait, not transport failure")
else:
    print("NO_MATCH: ask a focused question about cache invalidation, DB pool, capacity, consumers, provider, config, or network.")
