#!/usr/bin/env python3
import re, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
q=" ".join(sys.argv[2:]).strip().lower()
m=re.search(r"-t(\d+)(?:$|[^0-9])", root.name)
trial=int(m.group(1)) if m else 1
variant=((trial-1)%3)+1

def anyof(*xs): return any(x in q for x in xs)
def allof(*xs): return all(x in q for x in xs)

if not q or q in {"help","?","commands"} or allof("show","all") or "everything" in q:
    print("PROBE_GUIDANCE: ask one focused diagnostic question or controlled experiment.")
    raise SystemExit(0)

responses={
1:{
 "overview":"http failures=49/200; duplicate provider business effects=4/200 retry scenarios; stale reads=0",
 "http_by_pod":"api-a=0/100; api-b=49/100; failures occur before provider invocation",
 "api_a":"api-a app=52 rendered-config=24 desired=24 payment_mode=tokenized; normal checkout healthy",
 "api_b":"api-b app=52 rendered-config=23 desired=24 payment_mode=<missing>; affected requests reject before provider call",
 "retry_a":"healthy-pod timeout experiment: provider accepted first attempt, response timed out, retry used a different delivery-scoped key; provider recorded 2 logical effects for one order version",
 "retry_b":"api-b cannot isolate retry behavior because request fails before provider",
 "dup_boundary":"duplicates first appear at provider boundary in timeout/retry scenarios; fulfillment adds none",
 "consumer":"both consumer revisions accept current additive event schema; replay compatibility passes",
 "cache":"mixed invalidators pass compatibility bridge checks; stale read-after-write=0/10000",
 "capacity":"api cpu max=33%; queue=0; db pool=44%; no saturation correlation",
 "primary":"strict primary read is fresh",
 "replica":"strict replica read is fresh",
},
2:{
 "overview":"http failures=42/200 during peaks; provider duplicates=0; fulfillment duplicates=6/200 retries; stale reads=0",
 "http_by_pod":"api-a=20/100; api-b=22/100; errors correlate with queue depth rather than pod identity",
 "api_a":"api-a config=24 desired=24; no behavior delta",
 "api_b":"api-b config=23-equivalent; semantic active-key diff versus desired=none",
 "retry_a":"provider timeout retry reuses one business key; logical effects=1",
 "retry_b":"provider timeout retry reuses one business key; logical effects=1",
 "dup_boundary":"provider logical effects=1; duplicates first appear in fulfillment on consumer-2 during legal redelivery",
 "consumer":"consumer-1 rev=41 uses order-version dedupe; consumer-2 rev=39 uses delivery-id dedupe and can fulfill one order version twice",
 "cache":"mixed invalidators pass compatibility checks; stale read-after-write=0",
 "capacity":"api cpu=98-100%; request queue peaks at 61; saturation aligns with 503 windows; adding one replica removes test 503s",
 "primary":"fresh",
 "replica":"fresh",
},
3:{
 "overview":"http success=200/200; duplicate effects=0; read-after-write stale responses=17/500",
 "http_by_pod":"api-a=0 failures; api-b=0 failures",
 "api_a":"api-a config=24 desired=24; strict customer read route points to replica",
 "api_b":"api-b config=24 desired=24; strict customer read route points to replica",
 "retry_a":"provider logical effects=1",
 "retry_b":"provider logical effects=1",
 "dup_boundary":"provider=0 duplicate effects; fulfillment=0",
 "consumer":"consumer compatibility and replay pass",
 "cache":"legacy-writer scenario leaves stable-key alias stale only through invalidator-b rev=10; invalidator-a dual namespace passes",
 "capacity":"cpu max=36%; queues and pools healthy",
 "primary":"strict primary read is fresh immediately after write",
 "replica":"strict replica read can remain stale 300-900ms after commit",
}
}[variant]

kind=None
if anyof("overview","status","health","symptom"):
    kind="overview"
elif (anyof("500","http","error","failure") and anyof("pod","api-a","api-b","distribution","slice","which")):
    kind="http_by_pod"
elif "api-a" in q and anyof("timeout","retry","replay","experiment","inject"):
    kind="retry_a"
elif "api-b" in q and anyof("timeout","retry","replay","experiment","inject"):
    kind="retry_b"
elif anyof("duplicate","effect","idempot") and anyof("boundary","provider","fulfillment","where","first"):
    kind="dup_boundary"
elif anyof("consumer","fulfillment","event contract","redelivery","dedupe"):
    kind="consumer"
elif anyof("cache","invalidator","stale read","alias","invalidation"):
    kind="cache"
elif anyof("capacity","cpu","queue depth","saturation","scale","replica count"):
    kind="capacity"
elif anyof("primary","writer") and anyof("strict","read","fresh","experiment","compare"):
    kind="primary"
elif anyof("replica","lag") and anyof("strict","read","fresh","experiment","compare"):
    kind="replica"
elif "api-b" in q and anyof("config","configuration","rendered","payment_mode","log","request"):
    kind="api_b"
elif "api-a" in q and anyof("config","configuration","rendered","payment_mode","log","request"):
    kind="api_a"

if kind is None:
    print("NO_MATCH: request is too broad or does not isolate one observable. Ask a focused comparison, component inspection, or controlled experiment.")
    raise SystemExit(0)

print(responses[kind])
