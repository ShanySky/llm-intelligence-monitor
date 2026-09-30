import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const task = String(process.argv[2] ?? '').trim();
const taskDir = path.resolve(process.argv[3] ?? '.');
if (!task) throw new Error('task is required');
if (!fs.existsSync(taskDir)) throw new Error('task workspace not found: ' + taskDir);

const repoRoot = process.cwd();
const candidates = [
  path.join(repoRoot, 'benchmarks', task, 'blackbox_validate.py'),
  path.join(repoRoot, 'scripts', 'validators', task + '.py'),
];

const source = candidates.find((p) => fs.existsSync(p));
if (!source) {
  console.log('No opaque validator for ' + task);
  process.exit(0);
}

const safeTask = task.replace(/[^A-Za-z0-9_.-]+/g, '-');
const external = path.join(os.tmpdir(), 'llm-monitor-validator-' + safeTask + '.py');
fs.copyFileSync(source, external);
fs.chmodSync(external, 0o700);

const shellQuote = (value) => "'" + String(value).replace(/'/g, "'\\''") + "'";
const wrapper = [
  '#!/usr/bin/env bash',
  'set -euo pipefail',
  'exec python3 ' + shellQuote(external) + ' "$PWD" "$@"',
  '',
].join('\n');

const wrapperPath = path.join(taskDir, 'validate');
fs.writeFileSync(wrapperPath, wrapper);
fs.chmodSync(wrapperPath, 0o755);

console.log('Installed opaque ./validate for ' + task);
