#!/usr/bin/env bash
set -euo pipefail
rm -rf stage2-out
mkdir stage2-out
javac -d stage2-out src/*.java
java -cp stage2-out VisibleTest
java -cp stage2-out PartnerCompatibilityProbe
