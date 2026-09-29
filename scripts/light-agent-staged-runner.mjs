import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const taskDir = path.resolve(process.argv[2] ?? '.');
const model = process.argv[3] ?? process.env.BENCHMARK_MODEL ?? 'gpt-6-sol';
const effort = process.argv[4] ?? process.env.BENCHMARK_EFFORT ?? 'medium';
const outFile = process.argv[5] ?? 'staged-agent-result.json';

const baseUrl = String(process.env.OPENAI_BASE_URL ?? '').replace(/\/$/, '');
const apiKey = process.env.BENCHMARK_API_KEY ?? process.env.OPENAI_API_KEY ?? '';
if (!baseUrl || !apiKey) throw new Error('OPENAI_BASE_URL and BENCHMARK_API_KEY/OPENAI_API_KEY are required');

const stageFiles = ['TASK.md', 'STAGE2.md', 'STAGE3.md'].filter((name) =>
  fs.existsSync(path.join(taskDir, name))
);
if (!stageFiles.length) throw new Error('No staged task files found');

const instructions = [
  'You are a software engineering agent working in a small isolated task workspace.',
  'Use the shell tool to inspect files, edit files, and run tests.',
  'This task may arrive in multiple stages. Preserve earlier requirements unless a later stage explicitly changes them.',
  'When new evidence arrives, adapt the implementation rather than restarting blindly.',
  'Prefer minimal sufficient changes and preserve public interfaces.',
  'Validate after each stage before you conclude that stage.',
  'Do not access paths outside the current task workspace.',
].join('\n');

const tools = [{
  type: 'function',
  name: 'shell',
  description: 'Run one shell command inside the isolated task workspace.',
  parameters: {
    type: 'object',
    properties: { command: { type: 'string' } },
    required: ['command'],
    additionalProperties: false,
  },
  strict: true,
}];

const safeEnv = { ...process.env };
for (const key of Object.keys(safeEnv)) {
  if (/KEY|SECRET|TOKEN|PASSWORD|AUTH/i.test(key)) delete safeEnv[key];
}
safeEnv.PATH = process.env.PATH ?? '/usr/local/bin:/usr/bin:/bin';
safeEnv.HOME = taskDir;

let input = [];
let commands = [];
let totalUsage = { input_tokens: 0, output_tokens: 0, reasoning_tokens: 0, cached_input_tokens: 0 };
let responses = 0;
let apiRetries = 0;
let infrastructureError = null;
const stageResults = [];
const startedAt = Date.now();

async function callModel() {
  let lastError;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(baseUrl + '/responses', {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: 'Bearer ' + apiKey },
        body: JSON.stringify({
          model,
          reasoning: { effort },
          instructions,
          input,
          tools,
          tool_choice: 'auto',
          max_output_tokens: 4096,
          store: false,
        }),
      });
      const text = await response.text();
      if (response.ok) return JSON.parse(text);
      lastError = new Error('Responses API ' + response.status + ': ' + text.slice(0, 1000));
      if (!(response.status === 429 || response.status >= 500) || attempt === 2) throw lastError;
    } catch (error) {
      lastError = error;
      if (attempt === 2) throw error;
    }
    apiRetries += 1;
    await new Promise((resolve) => setTimeout(resolve, 1500 * (2 ** attempt)));
  }
  throw lastError;
}

function addUsage(u = {}) {
  totalUsage.input_tokens += Number(u.input_tokens ?? 0);
  totalUsage.output_tokens += Number(u.output_tokens ?? 0);
  totalUsage.cached_input_tokens += Number(u.input_tokens_details?.cached_tokens ?? 0);
  totalUsage.reasoning_tokens += Number(u.output_tokens_details?.reasoning_tokens ?? 0);
}

function runShell(command) {
  commands.push(command);
  if (commands.length > 32) return 'ERROR: shell action budget exceeded (32)';
  if (/\.\.|\/home\/|\/tmp\/|\/proc\/|\/etc\/|\bcurl\b|\bwget\b|\bprintenv\b|\benv\b|git\s+remote/i.test(command)) {
    return 'ERROR: command rejected by benchmark workspace isolation policy';
  }
  const result = spawnSync('/bin/bash', ['-lc', command], {
    cwd: taskDir,
    env: safeEnv,
    encoding: 'utf8',
    timeout: 30000,
    maxBuffer: 256 * 1024,
  });
  return [
    result.stdout ? 'STDOUT:\n' + result.stdout : '',
    result.stderr ? 'STDERR:\n' + result.stderr : '',
    'EXIT_CODE=' + (result.status ?? 124),
  ].filter(Boolean).join('\n').slice(0, 24000);
}

async function runStage(stageFile) {
  const stageText = fs.readFileSync(path.join(taskDir, stageFile), 'utf8');
  input.push({ role: 'user', content: [{ type: 'input_text', text: stageText }] });
  let finalText = '';
  const stageStart = Date.now();
  const commandStart = commands.length;

  for (let turn = 0; turn < 12; turn += 1) {
    const response = await callModel();
    responses += 1;
    addUsage(response.usage);
    const outputs = Array.isArray(response.output) ? response.output : [];
    const calls = outputs.filter((item) => item?.type === 'function_call' && item?.name === 'shell');
    const messages = outputs.filter((item) => item?.type === 'message');
    input.push(...outputs);

    if (calls.length) {
      for (const call of calls) {
        let args = {};
        try { args = JSON.parse(call.arguments ?? '{}'); } catch {}
        input.push({
          type: 'function_call_output',
          call_id: call.call_id,
          output: runShell(String(args.command ?? '')),
        });
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

  stageResults.push({
    stage: stageFile,
    duration_seconds: Math.round((Date.now() - stageStart) / 1000),
    shell_commands: commands.length - commandStart,
    final_text: finalText,
  });
}

try {
  for (const stageFile of stageFiles) {
    await runStage(stageFile);
  }
} catch (error) {
  infrastructureError = String(error?.message ?? error);
}

const result = {
  task_dir: taskDir,
  model,
  effort,
  duration_seconds: Math.round((Date.now() - startedAt) / 1000),
  stages: stageResults,
  responses,
  api_retries: apiRetries,
  infrastructure_error: infrastructureError,
  shell_commands: commands.length,
  usage: totalUsage,
};
fs.writeFileSync(path.resolve(outFile), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
if (infrastructureError) process.exitCode = 2;
