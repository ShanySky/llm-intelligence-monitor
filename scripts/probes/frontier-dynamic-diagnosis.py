#!/usr/bin/env python3
import re, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
query=" ".join(sys.argv[2:]).strip().lower()

m=re.search(r"-t(\d+)(?:$|[^0-9])", root.name)
trial=int(m.group(1)) if m else 1
variant=((trial-1)%3)+1

common_help="""queries:
overview
pods
slice http-errors by pod
slice duplicate-effects by boundary
slice stale-reads by path
component api-a
component api-b
component consumer-1
component consumer-2
component invalidator-a
component invalidator-b
experiment retry api-a
experiment retry api-b
experiment strict-read primary
experiment strict-read replica
capacity
queue
cache"""

variants={
1:{
 "overview":"http failures=49/200; duplicate provider business effects=4/200 retry scenarios; fulfillment duplicates=4/200 downstream of those provider duplicates; stale reads=0",
 "pods":"api-a app=52 config=24; api-b app=52 config=23; consumer-1 rev=41; consumer-2 rev=40; invalidator-a rev=12; invalidator-b rev=11",
 "slice http-errors by pod":"api-a=0/100; api-b=49/100; failures occur before provider invocation",
 "slice duplicate-effects by boundary":"provider logical effects >1 in 4 retry scenarios; fulfillment count exactly matches provider duplicates; no new duplicates introduced after event emission",
 "slice stale-reads by path":"primary=0; replica=0; cache=0",
 "component api-a":"rendered config=24 desired=24 payment_mode=tokenized",
 "component api-b":"rendered config=23 desired=24 payment_mode=<missing>; requests requiring payment_mode reject before provider call",
 "component consumer-1":"contract=3 additive schema accepted; order-key dedupe enabled",
 "component consumer-2":"contract=2 additive schema accepted in compatibility mode; replay test=pass",
 "component invalidator-a":"mode=dual; compatibility test=pass",
 "component invalidator-b":"rev=11 legacy-compatible bridge active; mixed-writer invalidation test=pass",
 "experiment retry api-a":"timeout after provider accept -> second attempt uses a different operation key; provider logical effects=2",
 "experiment retry api-b":"request rejected before provider; retry experiment never reaches provider",
 "experiment strict-read primary":"fresh",
 "experiment strict-read replica":"fresh",
 "capacity":"cpu max=33%; request queue=0; pool utilization=44%",
 "queue":"consumer replay does not add duplicates beyond provider-originated duplicates",
 "cache":"0 stale read-after-write failures in mixed-version sample"
},
2:{
 "overview":"http failures=42/200 during peaks; provider duplicate business effects=0; fulfillment duplicate business effects=6/200 retries; stale reads=0",
 "pods":"api-a app=52 config=24; api-b app=52 config=23-equivalent; consumer-1 rev=41; consumer-2 rev=39; invalidator-a rev=12; invalidator-b rev=11",
 "slice http-errors by pod":"api-a=20/100; api-b=22/100; errors correlate with queue depth, not pod identity",
 "slice duplicate-effects by boundary":"provider logical effects=1; event stream contains legal redeliveries; duplicates first appear in fulfillment on consumer-2",
 "slice stale-reads by path":"primary=0; replica=0; cache=0",
 "component api-a":"rendered config=24 desired=24; no behavior delta",
 "component api-b":"rendered config=23-equivalent; semantic diff versus desired=none for active keys",
 "component consumer-1":"rev=41 contract=3; replay uses order-version business dedupe",
 "component consumer-2":"rev=39 contract=1; replay uses delivery-id dedupe; same order-version redelivery can fulfill twice",
 "component invalidator-a":"mode=dual; compatibility test=pass",
 "component invalidator-b":"rev=11 compatibility bridge active; mixed-writer invalidation test=pass",
 "experiment retry api-a":"provider timeout retry reuses same business key; logical effects=1",
 "experiment retry api-b":"provider timeout retry reuses same business key; logical effects=1",
 "experiment strict-read primary":"fresh",
 "experiment strict-read replica":"fresh",
 "capacity":"cpu=98-100%; request queue spikes to 61; saturation windows align with 503s; one additional replica removes test 503s",
 "queue":"redelivery duplicates pinned to consumer-2 rev=39; consumer-1 replay=exactly-once business effect",
 "cache":"0 stale read-after-write failures"
},
3:{
 "overview":"http success=200/200; provider and fulfillment duplicate effects=0; read-after-write stale responses=17/500",
 "pods":"api-a app=52 config=24; api-b app=52 config=24; consumer-1 rev=41; consumer-2 rev=40-compatible; invalidator-a rev=12; invalidator-b rev=10",
 "slice http-errors by pod":"api-a=0; api-b=0",
 "slice duplicate-effects by boundary":"provider=0; fulfillment=0",
 "slice stale-reads by path":"persistent stale after legacy writer through cache=8; short-lived stale after v2 write when strict path uses replica=9",
 "component api-a":"config desired; strict customer read route currently points to replica",
 "component api-b":"config desired; strict customer read route currently points to replica",
 "component consumer-1":"contract=3 compatibility=pass",
 "component consumer-2":"contract=2 compatibility mode; replay=pass",
 "component invalidator-a":"rev=12 dual-namespace invalidation",
 "component invalidator-b":"rev=10 numeric-only invalidation; stable-key alias survives legacy writes",
 "experiment retry api-a":"provider logical effects=1",
 "experiment retry api-b":"provider logical effects=1",
 "experiment strict-read primary":"fresh immediately after write",
 "experiment strict-read replica":"stale for 300-900ms after commit",
 "capacity":"cpu max=36%; queue=0; pools healthy",
 "queue":"no duplicate business effects",
 "cache":"legacy-writer scenario leaves stable-key alias stale only when routed through invalidator-b"
}
}

if query=="help":
    print(common_help); raise SystemExit(0)
answer=variants[variant].get(query)
if answer is None:
    print("UNKNOWN_QUERY. Use 'help' for supported diagnostics.")
    raise SystemExit(2)
print(answer)
