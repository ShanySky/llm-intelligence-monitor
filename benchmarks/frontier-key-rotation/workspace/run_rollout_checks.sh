#!/usr/bin/env bash
set -euo pipefail
rm -rf rollout-out
mkdir rollout-out
javac -d rollout-out src/*.java
java -cp rollout-out RolloutProbe
