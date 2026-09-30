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

if not q or q in {"help","?","commands"} or "show all" in q or "everything" in q:
    print("PROBE_GUIDANCE: ask one focused observation or controlled experiment.")
    raise SystemExit(0)

v={
1:{
 "overview":"49/200 request failures; 4/200 timeout-retry scenarios create duplicate provider effects; failures correlate with api-b and zone-b",
 "observe_api":"api-a config=24 zone=a failures=0/100; api-b config=23 zone=b failures=49/100; api-b logs mention missing payment_mode; zone-b also has unrelated packet-loss warnings",
 "observe_retry":"duplicate business effects occur after provider timeouts; affected retries use different delivery identities; consumer-2 is also one revision behind",
 "network":"zone-b packet-loss warnings occur in background traffic, but successful checkout requests also traverse zone-b",
 "db":"db pool=46%, waiters=0",
 "intervene_config":"counterfactual replay on api-b with desired config=24 while staying in zone-b: 100/100 succeed; zone-b packet-loss background signal unchanged",
 "intervene_zone":"same api-b config=23 moved to zone-a: payment requests still fail before provider because payment_mode is missing",
 "intervene_key":"controlled timeout replay on healthy api-a: current delivery-scoped keys produce 2 provider effects; forcing one order-version key produces 1 effect with retries still enabled",
 "intervene_consumer":"replaying the resulting additive event through both consumers produces one fulfillment each; consumer revision does not create a second payment effect",
},
2:{
 "overview":"42/200 peak 503s; 6/200 fulfillment duplicates on redelivery; api-b config revision differs and consumer-2 is older",
 "observe_api":"api-a=20/100 peak 503; api-b=22/100 peak 503; api-b config=23-equivalent, active-key semantic diff versus desired=none",
 "observe_retry":"provider timeout retries preserve one business key; provider logical effects=1; duplicates first appear in fulfillment",
 "network":"transport healthy during 503 windows",
 "db":"db pool=49%, waiters=0",
 "observe_consumer":"consumer-1 order-version dedupe; consumer-2 delivery-id dedupe; both decode current schema",
 "intervene_capacity":"hold binary/config/traffic mix constant and add one API replica: test 503s fall from 21% to 0%; remove replica and 503s return",
 "intervene_config":"replace api-b with config=24-equivalent without changing capacity: 503 rate remains within noise",
 "intervene_consumer":"replay same order version with two delivery IDs: consumer-1 produces one fulfillment, consumer-2 produces two",
},
3:{
 "overview":"200/200 HTTP success; 0 duplicate effects; 17/500 strict read-after-write responses are stale; invalidator-b is older and strict reads use replica",
 "observe_cache":"legacy-writer stale cases retain stable-key cache alias; invalidator-b rev=10 is numeric-only; invalidator-a rev=12 is dual",
 "observe_reads":"some strict reads remain stale 300-900ms; ordinary reads are allowed to use replica",
 "network":"network healthy",
 "db":"db pool healthy; primary committed state is current",
 "intervene_cache":"hold read route on primary, write through legacy path: dual invalidator yields fresh read; numeric-only invalidator leaves stable-key alias stale",
 "intervene_replica":"bypass cache after v2 write: primary is immediately fresh while replica can remain stale 300-900ms",
 "intervene_flush":"global cache flush temporarily hides alias staleness but replica strict-read staleness remains",
}
}[variant]

if anyof("overview","status","symptom","health"):
    print(v["overview"]); raise SystemExit(0)

if anyof("counterfactual","intervention","experiment","control","hold constant","replay","force","bypass","move","replace","add replica"):
    if variant==1:
        if anyof("config","payment_mode","desired"): key="intervene_config"
        elif anyof("zone","host","network"): key="intervene_zone"
        elif anyof("idempot","key","retry","provider","order version"): key="intervene_key"
        elif anyof("consumer","fulfillment"): key="intervene_consumer"
        else: key=None
    elif variant==2:
        if anyof("capacity","replica","scale","503"): key="intervene_capacity"
        elif anyof("config","api-b"): key="intervene_config"
        elif anyof("consumer","redelivery","delivery id","fulfillment"): key="intervene_consumer"
        else: key=None
    else:
        if anyof("cache","invalidator","alias","legacy"): key="intervene_cache"
        elif anyof("replica","primary","strict read","bypass"): key="intervene_replica"
        elif anyof("flush"): key="intervene_flush"
        else: key=None
    if key:
        print(v[key]); raise SystemExit(0)

if variant==1:
    if anyof("api","pod","config","500","failure"): key="observe_api"
    elif anyof("retry","duplicate","provider","consumer"): key="observe_retry"
    elif anyof("network","zone","packet"): key="network"
    elif anyof("db","database","pool"): key="db"
    else: key=None
elif variant==2:
    if anyof("api","pod","config","503","failure","capacity"): key="observe_api"
    elif anyof("retry","duplicate","provider"): key="observe_retry"
    elif anyof("consumer","fulfillment","redelivery"): key="observe_consumer"
    elif anyof("network"): key="network"
    elif anyof("db","database","pool"): key="db"
    else: key=None
else:
    if anyof("cache","invalidator","alias","legacy"): key="observe_cache"
    elif anyof("read","replica","primary","stale"): key="observe_reads"
    elif anyof("network"): key="network"
    elif anyof("db","database","pool"): key="db"
    else: key=None

if key:
    print(v[key]); raise SystemExit(0)

print("NO_MATCH: ask a focused observation or controlled experiment that isolates one hypothesis.")
