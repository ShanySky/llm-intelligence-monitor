#!/usr/bin/env python3
import re, sys

q=" ".join(sys.argv[2:]).strip().lower()
words=set(re.findall(r"[a-z0-9_-]+", q))

def has(*xs):
    return all(x in q for x in xs)

# Deliberately no command catalog. Broad discovery requests do not reveal one.
if not q or q in {"help","?","commands"} or has("show","all") or "everything" in q:
    print("PROBE_GUIDANCE: ask one focused question about a component, comparison, log, or experiment.")
    raise SystemExit(0)

if any(x in q for x in ["status","overview","symptom","health"]):
    print("checkout sample: 151/200 2xx, 49/200 500; timeout-replay: 4 duplicate provider effects / 200; p95 normal; stale-cache signal absent")
    raise SystemExit(0)

if ("pod" in q or "api" in q) and any(x in q for x in ["compare","revision","version","rollout"]):
    print("api-a app=52 rendered-config=24; api-b app=52 rendered-config=23; desired rendered-config=24")
    raise SystemExit(0)

if "api-b" in q and any(x in q for x in ["config","configuration","rendered","payment_mode"]):
    print("api-b rendered-config=23 desired=24 payment_mode=<missing> retries=enabled")
    raise SystemExit(0)

if "api-a" in q and any(x in q for x in ["config","configuration","rendered","payment_mode"]):
    print("api-a rendered-config=24 desired=24 payment_mode=tokenized retries=enabled")
    raise SystemExit(0)

if "api-b" in q and any(x in q for x in ["log","error","500","request"]):
    print("api-b: request rejected before provider call because payment_mode is absent in rendered config")
    raise SystemExit(0)

if "api-a" in q and any(x in q for x in ["log","error","500","request"]) and not any(x in q for x in ["timeout","retry"]):
    print("api-a: normal checkout path healthy; no pod-local 500 signature")
    raise SystemExit(0)

if "api-a" in q and any(x in q for x in ["timeout","retry","replay","experiment","inject"]):
    print("healthy-pod timeout experiment: first provider attempt accepted then response timed out; retry used a different delivery-scoped key; provider recorded 2 logical effects")
    raise SystemExit(0)

if "api-b" in q and any(x in q for x in ["timeout","retry","replay","experiment","inject"]):
    print("api-b timeout experiment is not isolating: request fails before reaching provider because rendered config is invalid")
    raise SystemExit(0)

if any(x in q for x in ["provider","ledger","payment effect","payment-effect","effects"]):
    print("provider ledger: duplicates are created at provider boundary only in timeout/retry cases; affected retries carry different delivery identities for the same order version")
    raise SystemExit(0)

if any(x in q for x in ["consumer","event contract","decode"]):
    print("consumer-1 rev=41 contract=3; consumer-2 rev=40 contract=2-compatible; both accept current additive event schema; reject/decode errors=0")
    raise SystemExit(0)

if any(x in q for x in ["queue","fulfillment"]):
    print("fulfillment queue: duplicate customer-visible payment effects already exist upstream before consumption; fulfillment does not create a second payment")
    raise SystemExit(0)

if any(x in q for x in ["cache","invalidator","stale read"]):
    print("mixed invalidator revisions active; compatibility bridge receives numeric + stable-key invalidations; stale read-after-write failures=0/10000")
    raise SystemExit(0)

if any(x in q for x in ["capacity","cpu","scale","replica","latency"]):
    print("capacity: max API CPU=31%, request queue=0, p95 normal, replica headroom available")
    raise SystemExit(0)

if any(x in q for x in ["database","db","pool","connection"]):
    print("database: pool utilization=42%, waiters=0, query latency normal")
    raise SystemExit(0)

if any(x in q for x in ["network","dns","packet","connectivity"]):
    print("network: DNS and provider connectivity healthy outside injected timeout experiments; no correlated transport failures")
    raise SystemExit(0)

print("NO_MATCH: request was too vague for the diagnostic interface. Ask a focused question about one component, comparison, log, or experiment.")
raise SystemExit(0)
