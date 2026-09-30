import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const taskDir = path.resolve(process.argv[2] ?? '.');
const model = process.argv[3] ?? process.env.BENCHMARK_MODEL ?? 'gpt-6-sol';
const effort = process.argv[4] ?? process.env.BENCHMARK_EFFORT ?? 'medium';
const outFile = process.argv[5] ?? 'light-agent-result.json';

const baseUrl = String(process.env.OPENAI_BASE_URL ?? '').replace(/\/$/, '');
const apiKey = process.env.BENCHMARK_API_KEY ?? process.env.OPENAI_API_KEY ?? '';
if (!baseUrl || !apiKey) throw new Error('OPENAI_BASE_URL and BENCHMARK_API_KEY/OPENAI_API_KEY are required');
if (!['medium', 'high', 'xhigh'].includes(effort)) throw new Error('Unsupported effort');

const taskPath = path.join(taskDir, 'TASK.md');
if (!fs.existsSync(taskPath)) throw new Error('TASK.md not found');
const task = fs.readFileSync(taskPath, 'utf8');
const dockerContainer = String(process.env.AGENT_DOCKER_CONTAINER ?? '').trim();
const dockerWorkdir = String(process.env.AGENT_DOCKER_WORKDIR ?? '/app').trim() || '/app';
const containerMode = Boolean(dockerContainer);
const validationCommand = String(process.env.AGENT_VALIDATION_COMMAND ?? '').trim();
const validationBudget = Number(process.env.AGENT_VALIDATION_BUDGET ?? 8);
const probeScript = String(process.env.AGENT_PROBE_SCRIPT ?? '').trim();
const probeBudget = Number(process.env.AGENT_PROBE_BUDGET ?? 12);

const instructions = (
  containerMode
    ? [
        'You are a software engineering agent operating inside a disposable benchmark container.',
        'Use the shell tool to inspect and modify the container as needed to complete the task.',
        'All shell commands run inside the benchmark container; system paths such as /etc and /var are container-local.',
        'Do not try to access the Docker control plane or the host environment.',
        'Work toward the actual task requirements and validate the final behavior before finishing.',
        'When finished, give a concise summary and the validation commands you ran.',
      ]
    : [
        'You are a software engineering agent working in a small isolated task workspace.',
        'Use the shell tool to inspect files, edit files, and run tests.',
        'Work toward the actual task requirements, not merely the visible test.',
        'Prefer minimal sufficient changes. Preserve public interfaces unless the task explicitly permits changes.',
        'Validate your work before finishing.',
        'Do not access paths outside the current task workspace.',
        'When finished, give a concise summary and the validation commands you ran.',
      ]
).join('\n');

const tools = [{
  type: 'function',
  name: 'shell',
  description: 'Run one shell command inside the isolated task workspace. Use it to inspect, edit, and test files.',
  parameters: {
    type: 'object',
    properties: {
      command: { type: 'string', description: 'Bash command to run in the task workspace.' },
    },
    required: ['command'],
    additionalProperties: false,
  },
  strict: true,
}];

if (validationCommand) {
  tools.push({
    type: 'function',
    name: 'validate',
    description: 'Run the benchmark-provided black-box validation against the current workspace. Use its failure output as evidence, fix the implementation, and rerun as needed.',
    parameters: {
      type: 'object',
      properties: {},
      additionalProperties: false,
    },
    strict: true,
  });
}

if (probeScript) {
  tools.push({
    type: 'function',
    name: 'probe',
    description: 'Query the benchmark-provided opaque runtime diagnostic interface. Use focused queries to gather evidence before changing the workspace.',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Task-specific diagnostic query.' },
      },
      required: ['query'],
      additionalProperties: false,
    },
    strict: true,
  });
}

const safeEnv = { ...process.env };
for (const key of Object.keys(safeEnv)) {
  if (/KEY|SECRET|TOKEN|PASSWORD|AUTH/i.test(key) || /^GITHUB_/i.test(key) || /^RUNNER_/i.test(key)) {
    delete safeEnv[key];
  }
}
delete safeEnv.AGENT_VALIDATION_COMMAND;
delete safeEnv.AGENT_VALIDATION_BUDGET;
delete safeEnv.AGENT_PROBE_SCRIPT;
delete safeEnv.AGENT_PROBE_BUDGET;
safeEnv.PATH = process.env.PATH ?? '/usr/local/bin:/usr/bin:/bin';
safeEnv.HOME = taskDir;

const maxTurns = Number(process.env.AGENT_MAX_TURNS ?? 16);
const shellBudget = Number(process.env.AGENT_SHELL_BUDGET ?? 24);
const maxOutputTokens = Number(process.env.AGENT_MAX_OUTPUT_TOKENS ?? 4096);
const shellTimeoutMs = Number(process.env.AGENT_SHELL_TIMEOUT_MS ?? 30000);

let input = [{ role: 'user', content: [{ type: 'input_text', text: task }] }];
let totalUsage = { input_tokens: 0, output_tokens: 0, reasoning_tokens: 0, cached_input_tokens: 0 };
let commands = [];
let validationCalls = 0;
let probeCalls = 0;
let probeAttempts = 0;
let probeQueries = [];
let probeExecutedQueries = [];
let probeObservations = [];
let finalText = '';
let responses = 0;
let apiRetries = 0;
let infrastructureError = null;
const startedAt = Date.now();

const snapshotIgnore = (rel) =>
  /(^|\/)(?:\.git|out|hidden-out|node_modules)(?:\/|$)/.test(rel) ||
  /(?:^|\/)(?:light-agent-result|score)\.json$/.test(rel) ||
  /\.class$/.test(rel);

function snapshotWorkspace(root) {
  const snap = new Map();
  function walk(dir) {
    for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, ent.name);
      const rel = path.relative(root, full).replace(/\\/g, '/');
      if (snapshotIgnore(rel)) continue;
      if (ent.isDirectory()) {
        walk(full);
      } else if (ent.isFile()) {
        try {
          const stat = fs.statSync(full);
          if (stat.size > 1024 * 1024) continue;
          const buf = fs.readFileSync(full);
          if (buf.includes(0)) continue;
          snap.set(rel, buf.toString('utf8'));
        } catch {}
      }
    }
  }
  walk(root);
  return snap;
}

function changedLineCount(beforeText, afterText) {
  const a = String(beforeText ?? '').split(/\r?\n/);
  const b = String(afterText ?? '').split(/\r?\n/);
  if (a.length * b.length > 250000) {
    return Math.abs(a.length - b.length) + Math.min(a.length, b.length);
  }
  const dp = new Array(b.length + 1).fill(0);
  for (let i = 1; i <= a.length; i += 1) {
    let prev = 0;
    for (let j = 1; j <= b.length; j += 1) {
      const old = dp[j];
      if (a[i - 1] === b[j - 1]) dp[j] = prev + 1;
      else dp[j] = Math.max(dp[j], dp[j - 1]);
      prev = old;
    }
  }
  const lcs = dp[b.length];
  return (a.length - lcs) + (b.length - lcs);
}

function diffWorkspace(before, after) {
  const files = [...new Set([...before.keys(), ...after.keys()])].sort();
  const changes = [];
  for (const rel of files) {
    const hasBefore = before.has(rel);
    const hasAfter = after.has(rel);
    if (hasBefore && hasAfter && before.get(rel) === after.get(rel)) continue;
    const kind = !hasBefore ? 'added' : (!hasAfter ? 'deleted' : 'modified');
    const changedLines = changedLineCount(before.get(rel) ?? '', after.get(rel) ?? '');
    changes.push({ path: rel, kind, changed_lines: changedLines });
  }
  return {
    changed_files: changes.length,
    changed_lines: changes.reduce((sum, x) => sum + Number(x.changed_lines ?? 0), 0),
    added_files: changes.filter((x) => x.kind === 'added').length,
    deleted_files: changes.filter((x) => x.kind === 'deleted').length,
    files: changes,
  };
}

const initialWorkspaceSnapshot = snapshotWorkspace(taskDir);

async function callModel() {
  let lastError = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(baseUrl + '/responses', {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          authorization: 'Bearer ' + apiKey,
        },
        body: JSON.stringify({
          model,
          reasoning: { effort },
          instructions,
          input,
          tools,
          tool_choice: 'auto',
          max_output_tokens: maxOutputTokens,
          store: false,
        }),
      });
      const text = await response.text();
      if (response.ok) return JSON.parse(text);

      lastError = new Error('Responses API ' + response.status + ': ' + text.slice(0, 1000));
      if (!(response.status === 429 || response.status >= 500) || attempt === 2) {
        throw lastError;
      }
    } catch (error) {
      lastError = error;
      if (attempt === 2) throw error;
    }

    apiRetries += 1;
    await new Promise((resolve) => setTimeout(resolve, 1500 * (2 ** attempt)));
  }
  throw lastError ?? new Error('Unknown Responses API failure');
}

function addUsage(u = {}) {
  totalUsage.input_tokens += Number(u.input_tokens ?? 0);
  totalUsage.output_tokens += Number(u.output_tokens ?? 0);
  totalUsage.cached_input_tokens += Number(u.input_tokens_details?.cached_tokens ?? 0);
  totalUsage.reasoning_tokens += Number(u.output_tokens_details?.reasoning_tokens ?? 0);
}

function runShell(command) {
  commands.push(command);
  if (commands.length > shellBudget) return `ERROR: shell action budget exceeded (${shellBudget})`;

  let executable = '/bin/bash';
  let args = ['-lc', command];

  if (containerMode) {
    if (/\bdocker\b/i.test(command)) {
      return 'ERROR: Docker control-plane access is not available inside the benchmark container';
    }
    executable = 'docker';
    args = ['exec', '-w', dockerWorkdir, dockerContainer, '/bin/bash', '-lc', command];
  } else if (/\.\.|\/home\/|\/tmp\/|\/proc\/|\/etc\/|\bcurl\b|\bwget\b|\bprintenv\b|\benv\b|git\s+remote|GITHUB_|RUNNER_/i.test(command)) {
    return 'ERROR: command rejected by benchmark workspace isolation policy';
  }

  const result = spawnSync(executable, args, {
    cwd: taskDir,
    env: safeEnv,
    encoding: 'utf8',
    timeout: shellTimeoutMs,
    maxBuffer: 256 * 1024,
  });
  const output = [
    result.stdout ? 'STDOUT:\n' + result.stdout : '',
    result.stderr ? 'STDERR:\n' + result.stderr : '',
    'EXIT_CODE=' + (result.status ?? 124),
  ].filter(Boolean).join('\n');
  return output.slice(0, 24000);
}

function runValidation() {
  validationCalls += 1;
  if (!validationCommand) return 'ERROR: black-box validation is not enabled for this task';
  if (validationCalls > validationBudget) {
    return `ERROR: validation action budget exceeded (${validationBudget})`;
  }

  const result = spawnSync('/bin/bash', ['-lc', validationCommand], {
    cwd: taskDir,
    env: safeEnv,
    encoding: 'utf8',
    timeout: shellTimeoutMs,
    maxBuffer: 256 * 1024,
  });
  const output = [
    result.stdout ? 'STDOUT:\n' + result.stdout : '',
    result.stderr ? 'STDERR:\n' + result.stderr : '',
    'EXIT_CODE=' + (result.status ?? 124),
  ].filter(Boolean).join('\n');
  return output.slice(0, 24000);
}

function runProbe(query) {
  const normalizedQuery = String(query ?? '');
  probeAttempts += 1;
  probeQueries.push(normalizedQuery);
  if (!probeScript) return 'ERROR: runtime probe is not enabled for this task';
  if (probeCalls >= probeBudget) {
    return 'ERROR: probe action budget exceeded (' + probeBudget + ')';
  }

  probeCalls += 1;
  probeExecutedQueries.push(normalizedQuery);
  const result = spawnSync('python3', [probeScript, taskDir, normalizedQuery], {
    cwd: taskDir,
    env: safeEnv,
    encoding: 'utf8',
    timeout: shellTimeoutMs,
    maxBuffer: 256 * 1024,
  });
  const output = [
    result.stdout ? 'STDOUT:\n' + result.stdout : '',
    result.stderr ? 'STDERR:\n' + result.stderr : '',
    'EXIT_CODE=' + (result.status ?? 124),
  ].filter(Boolean).join('\n');
  const clipped = output.slice(0, 24000);
  probeObservations.push({
    query: normalizedQuery,
    output: clipped,
    exit_code: result.status ?? 124,
  });
  return clipped;
}

try {
  for (let turn = 0; turn < maxTurns; turn += 1) {
    const response = await callModel();
    responses += 1;
    addUsage(response.usage);
  
    const outputs = Array.isArray(response.output) ? response.output : [];
    const calls = outputs.filter((item) =>
      item?.type === 'function_call' && (item?.name === 'shell' || item?.name === 'validate' || item?.name === 'probe')
    );
    const messages = outputs.filter((item) => item?.type === 'message');
  
    input.push(...outputs);
  
    if (calls.length) {
      for (const call of calls) {
        let args;
        try { args = JSON.parse(call.arguments ?? '{}'); }
        catch { args = {}; }
        const result = call.name === 'validate'
          ? runValidation()
          : call.name === 'probe'
            ? runProbe(String(args.query ?? ''))
            : runShell(String(args.command ?? ''));
        input.push({ type: 'function_call_output', call_id: call.call_id, output: result });
      }
      continue;
    }
  
    for (const message of messages) {
      for (const part of message.content ?? []) {
        if (part?.type === 'output_text' && typeof part.text === 'string') finalText += part.text;
      }
    }
    if (messages.length) break;
  }
  
} catch (error) {
  infrastructureError = String(error?.message ?? error);
}

const finalWorkspaceSnapshot = snapshotWorkspace(taskDir);
const patchMetrics = diffWorkspace(initialWorkspaceSnapshot, finalWorkspaceSnapshot);

const result = {
  task_dir: taskDir,
  model,
  effort,
  duration_seconds: Math.round((Date.now() - startedAt) / 1000),
  responses,
  api_retries: apiRetries,
  infrastructure_error: infrastructureError,
  shell_commands: commands.length,
  shell_budget: shellBudget,
  validation_calls: validationCalls,
  validation_budget: validationCommand ? validationBudget : 0,
  validation_enabled: Boolean(validationCommand),
  probe_calls: probeCalls,
  probe_attempts: probeAttempts,
  probe_budget: probeScript ? probeBudget : 0,
  probe_enabled: Boolean(probeScript),
  probe_queries: probeQueries,
  probe_executed_queries: probeExecutedQueries,
  probe_observations: probeObservations,
  patch_metrics: patchMetrics,
  max_turns: maxTurns,
  container_mode: containerMode,
  docker_container: containerMode ? dockerContainer : null,
  usage: totalUsage,
  final_text: finalText,
};
fs.writeFileSync(path.resolve(outFile), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
if (infrastructureError) process.exitCode = 2;
