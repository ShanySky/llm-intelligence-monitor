#!/usr/bin/env bash
set -euo pipefail
rm -rf out
mkdir out
javac -d out src/*.java
java -cp out VisibleTest
