import fs from 'node:fs';

const model = process.argv[2];
const label = process.argv[3];
const out = process.argv[4] ?? 'results/promptfoo-model.yaml';
const effort = process.argv[5] ?? 'xhigh';
const testFile = process.argv[6] ?? '../tests/selected.yaml';

if (!model || !label) {
  throw new Error('Usage: node scripts/build-model-config.mjs <model> <label> [output] [effort] [testFile]');
}
if (!['low', 'medium', 'high', 'xhigh'].includes(effort)) {
  throw new Error(`Unsupported reasoning effort: ${effort}`);
}

const yaml = `# AUTO-GENERATED for one model job.
description: GPT bilingual capability regression suite - ${label}

prompts:
  - "{{question}}"

providers:
  - id: openai:responses:${model}
    label: ${label}
    config:
      reasoning:
        effort: ${effort}
      max_output_tokens: 8192
      store: false
      maxRetries: 1

tests:
  - file://${testFile}

sharing: false

evaluateOptions:
  cache: false
  maxConcurrency: 2
  timeoutMs: 600000
`;

fs.mkdirSync('results', { recursive: true });
fs.writeFileSync(out, yaml);
console.log(`Generated ${out} for ${label} (${model}, ${effort}) using ${testFile}`);
