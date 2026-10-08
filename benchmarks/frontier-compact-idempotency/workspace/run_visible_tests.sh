#!/usr/bin/env bash
set -euo pipefail
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
javac -d "$out" src/*.java
java -cp "$out" VisibleTest
