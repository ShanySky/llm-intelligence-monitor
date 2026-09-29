#!/usr/bin/env python3
import json, sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = json.loads((root / "schema" / "fields.json").read_text())
out = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "generated" / "config.schema.json"

props = {}
for field in source:
    item = {"type": field["type"]}
    if "default" in field:
        item["default"] = field["default"]
    if "enum" in field:
        item["enum"] = field["enum"]
    props[field["name"]] = item

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "application-config",
    "type": "object",
    "additionalProperties": False,
    "properties": props,
}

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
