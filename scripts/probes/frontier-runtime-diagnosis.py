#!/usr/bin/env python3
import sys

query=" ".join(sys.argv[2:]).strip().lower()

responses={
  "help": """queries:
status
pods
config api-a
config api-b
logs api-a
logs api-b
experiment normal api-a
experiment normal api-b
experiment timeout api-a
experiment timeout api-b
consumers
queue
invalidators
cache
capacity""",
  "status": "checkout=151/200_2xx 49/200_500; retry-replay=4 duplicate provider effects / 200; p95=normal; cache-stale=0",
  "pods": """api-a app=52 rendered-config=24
api-b app=52 rendered-config=23
consumer-1 rev=41 contract=3
consumer-2 rev=40 contract=2-compatible
invalidator-a rev=12 mode=dual
invalidator-b rev=11 mode=legacy-compatible""",
  "config api-a": "rendered=24 desired=24 payment_mode=tokenized retries=enabled",
  "config api-b": "rendered=23 desired=24 payment_mode=<missing> retries=enabled",
  "logs api-a": "INFO checkout provider path healthy under normal traffic",
  "logs api-b": "ERROR payment_mode missing in rendered config; request rejected before provider call",
  "experiment normal api-a": "200 OK; provider logical effects=1 attempts=1",
  "experiment normal api-b": "500 before provider call; provider logical effects=0",
  "experiment timeout api-a": "request eventually succeeds after retry; provider logical effects=2 attempts=2; retry delivery ids differ",
  "experiment timeout api-b": "500 before provider call; timeout injection never reaches provider",
  "consumers": "consumer-1 and consumer-2 both accept current additive event schema; no reject/decode errors",
  "queue": "duplicate customer-visible effects are already present at payment provider boundary before fulfillment consumption",
  "invalidators": "mixed revisions active; compatibility bridge receives both numeric and stable-key invalidations",
  "cache": "0 stale read-after-write failures in 10k mixed-version samples",
  "capacity": "api cpu=31% max; request queue=0; db pool=42% utilized; scaling headroom available"
}

if query in responses:
    print(responses[query])
    raise SystemExit(0)

print("UNKNOWN_QUERY. Use probe query 'help' for supported diagnostics.")
raise SystemExit(2)
