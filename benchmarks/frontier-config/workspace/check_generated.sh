#!/usr/bin/env bash
set -euo pipefail
tmp="$(mktemp)"
python3 scripts/generate_schema.py "$tmp"
cmp -s "$tmp" generated/config.schema.json || {
  echo "generated/config.schema.json is stale; regenerate from schema/fields.json" >&2
  diff -u generated/config.schema.json "$tmp" || true
  rm -f "$tmp"
  exit 1
}
rm -f "$tmp"
echo "GENERATED_SCHEMA_OK"
