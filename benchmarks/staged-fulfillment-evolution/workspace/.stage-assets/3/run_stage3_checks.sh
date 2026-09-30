#!/usr/bin/env bash
set -euo pipefail
rm -rf stage3-out
mkdir stage3-out
javac -d stage3-out src/*.java
java -cp stage3-out VisibleTest
java -cp stage3-out MultiItemProbe
java -cp stage3-out RedeliveryProbe
