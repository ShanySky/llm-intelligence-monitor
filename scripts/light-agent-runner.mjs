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

const instructions = [
  'You are a software engineering agent working in a small isolated task workspace.',
  'Use the shell tool to inspect files, edit files, and run tests.',
  'Work toward the actual task requirements, not merely the visible test.',
  'Prefer minimal sufficient changes. Preserve public interfaces unless the task explicitly permits changes.',
  'Validate your work before finishing.',
  'Do not access paths outside the current task workspace.',
  'When finished, give a concise summary and the validation commands you ran.',
].join('\n');

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

const safeEnv = { ...process.env };
for (const key of Object.keys(safeEnv)) {
  if (/KEY|SECRET|TOKEN|PASSWORD|AUTH/i.test(key)) delete safeEnv[key];
}
safeEnv.PATH = process.env.PATH ?? '/usr/local/bin:/usr/bin:/bin';
safeEnv.HOME = taskDir;

const maxTurns = Number(process.env.AGENT_MAX_TURNS ?? 16);
const shellBudget = Number(process.env.AGENT_SHELL_BUDGET ?? 24);
const maxOutputTokens = Number(process.env.AGENT_MAX_OUTPUT_TOKENS ?? 4096);

let input = [{ role: 'user', content: [{ type: 'input_text', text: task }] }];
let totalUsage = { input_tokens: 0, output_tokens: 0, reasoning_tokens: 0, cached_input_tokens: 0 };
let commands = [];
let finalText = '';
let responses = 0;
let apiRetries = 0;
let infrastructureError = null;
const startedAt = Date.now();

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
  const output = [
    result.stdout ? 'STDOUT:\n' + result.stdout : '',
    result.stderr ? 'STDERR:\n' + result.stderr : '',
    'EXIT_CODE=' + (result.status ?? 124),
  ].filter(Boolean).join('\n');
  return output.slice(0, 24000);
}

try {
  for (let turn = 0; turn < maxTurns; turn += 1) {
    const response = await callModel();
    responses += 1;
    addUsage(response.usage);
  
    const outputs = Array.isArray(response.output) ? response.output : [];
    const calls = outputs.filter((item) => item?.type === 'function_call' && item?.name === 'shell');
    const messages = outputs.filter((item) => item?.type === 'message');
  
    input.push(...outputs);
  
    if (calls.length) {
      for (const call of calls) {
        let args;
        try { args = JSON.parse(call.arguments ?? '{}'); }
        catch { args = {}; }
        const result = runShell(String(args.command ?? ''));
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
  max_turns: maxTurns,
  usage: totalUsage,
  final_text: finalText,
};
fs.writeFileSync(path.resolve(outFile), JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify(result, null, 2));
if (infrastructureError) process.exitCode = 2;
