#!/usr/bin/env bash
set -euo pipefail
node stage2-check.js
./run_stage1_checks.sh
