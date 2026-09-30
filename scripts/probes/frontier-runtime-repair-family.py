#!/usr/bin/env python3
import re, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
q=" ".join(sys.argv[2:]).strip().lower()
m=re.search(r"-t(\d+)(?:$|[^0-9])", root.name)
trial=int(m.group(1)) if m else 1
variant=((trial-1)%3)+1

def anyof(*xs):
    return any(x in q for x in xs)

if not q or q in {"help","?","commands"} or "show all" in q or "everything" in q:
    print("PROBE_GUIDANCE: ask one focused question about a symptom, boundary, or controlled experiment.")
    raise SystemExit(0)

if variant == 1:
    if anyof("overview","status","symptom","health"):
        print("normal payments succeed; duplicate provider business effects occur only after timeout/crash retry with a new delivery id")
    elif anyof("provider","boundary","duplicate","idempot"):
        print("duplicates first appear at provider boundary: same order=o-17 version=7 produced keys delivery:d-81 then delivery:d-82 and two logical effects")
    elif anyof("timeout","crash","retry","experiment"):
        print("controlled retry: first charge accepted, process failed before local completion; retry used new delivery id and provider accepted a second effect")
    elif anyof("downstream","fulfillment","queue","cache","database"):
        print("downstream consumers add no extra payment effects; storage and cache are healthy for this incident")
    else:
        print("NO_MATCH: ask about provider boundary, timeout/crash retry, or another concrete subsystem.")
elif variant == 2:
    if anyof("overview","status","symptom","health"):
        print("two stale-read signatures: v2 read after a legacy writer can return an old cached value; strict read-after-write can return old replica data")
    elif anyof("cache","alias","legacy writer","invalidation"):
        print("legacy writer updated primary row alice->bob; numeric alias was invalidated but stable:key-1 remained cached as alice; primary row is bob")
    elif anyof("bypass","primary","cache off","cache bypass"):
        print("with cache bypassed, primary read returns bob immediately; the stable-key cache alias is the stale layer")
    elif anyof("strict","replica","lag","read-after-write"):
        print("controlled strict-read experiment: primary=v2 immediately after commit, replica remains v1 until replication; strict path currently returned replica=v1")
    elif anyof("ordinary","eventual"):
        print("ordinary read is allowed to use the replica and may temporarily return v1")
    else:
        print("NO_MATCH: ask about cache aliases, legacy writer invalidation, primary/replica, or a strict-read experiment.")
else:
    if anyof("overview","status","symptom","health"):
        print("migration validation shows occasional status rollback after live writes and loss of stable customer identity after legacy-version updates")
    elif anyof("backfill","delayed","version","race"):
        print("captured backfill item: id=7 status=OPEN version=5; live v2 write committed PAID version=6; delayed backfill later restored OPEN/version=5")
    elif anyof("legacy","stable key","identity","rollback"):
        print("customer id=9 had stableKey=key-9 before a legacy writer update; after the update stableKey became null while legacy status/version advanced")
    elif anyof("v2","live write","current row"):
        print("v2 live writes preserve stableKey and advance both status representations with a higher version")
    else:
        print("NO_MATCH: ask about delayed backfill, live-write versions, legacy writer compatibility, or stable identity.")

raise SystemExit(0)
