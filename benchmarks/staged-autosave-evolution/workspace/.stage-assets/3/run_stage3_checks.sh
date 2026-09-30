#!/usr/bin/env bash
set -euo pipefail
node stage3-check.js
./run_stage2_checks.sh
./run_visible_tests.sh
