#!/usr/bin/env python3
import sys
q=" ".join(sys.argv[2:]).strip().lower()
if not q or q in {"help","?","commands"} or "everything" in q or "show all" in q:
    print("PROBE_GUIDANCE: ask one focused question about load/capacity, a component, an event retry experiment, or another causal hypothesis.")
elif any(x in q for x in ["status","overview","symptom","health"]):
    print("burst sample: p95=2.8s, 23/200 requests=503; fulfillment replay=6 duplicate business effects/200; payment provider duplicate effects=0; stale-cache=0")
elif any(x in q for x in ["experiment","counterfactual","hold constant","controlled"]) and any(x in q for x in ["capacity","replica","burst","scale"]):
    print("controlled replica experiment: hold image, config, traffic and DB constant; adding one API replica makes p95=310ms and 503 falls to 0; removing replica restores 503 failures")
elif any(x in q for x in ["experiment","counterfactual","controlled","replay"]) and any(x in q for x in ["consumer","fulfillment","delivery","dedup","event"]):
    print("controlled delivery replay: hold business order version fixed, change only delivery id; consumer-1 produces one effect; consumer-2 produces two effects; changing revision without dedupe change does not repair the event")
elif any(x in q for x in ["capacity","cpu","queue","load","replica","burst"]):
    print("API observation: both pods CPU 96-99%, request queue peaks 143, DB pool 47%, provider latency normal; root cause not established without intervention")
elif ("consumer" in q or "fulfillment" in q) and any(x in q for x in ["retry","replay","experiment","duplicate","dedup"]):
    print("Consumer observation: consumer-1 rev=41 and consumer-2 rev=40; both decode events, and duplicates correlate with redeliveries; use a controlled replay to isolate causal dedupe semantics")
elif "consumer" in q or "event" in q:
    print("consumer-1 rev=41 contract=3; consumer-2 rev=40 contract=2; both decode the additive schema, but decode success alone does not test retry semantics")
elif any(x in q for x in ["provider","payment","idempot"]):
    print("payment provider: timeout retries reuse stable order-version key; duplicate provider effects=0")
elif any(x in q for x in ["database","db","pool","connection"]):
    print("database pool utilization=47%, waiters=0, query latency normal during burst")
elif any(x in q for x in ["config","api-a","api-b","rendered"]):
    print("api-a and api-b rendered config both match desired revision 24; no payment_mode drift")
elif any(x in q for x in ["cache","invalidator","stale"]):
    print("cache compatibility bridge healthy; stale read-after-write=0/10000")
elif any(x in q for x in ["network","dns","connectivity"]):
    print("network/DNS healthy; no correlated transport errors during burst")
else:
    print("NO_MATCH: ask a focused question about load/capacity, consumer replay, provider, database, config, cache, or network.")
