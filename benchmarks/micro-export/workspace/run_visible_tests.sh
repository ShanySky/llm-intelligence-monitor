#!/usr/bin/env bash
set -euo pipefail
rm -rf out
mkdir -p out
javac -d out src/*.java
java -cp out VisibleTest
