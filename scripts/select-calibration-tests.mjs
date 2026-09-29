import fs from 'node:fs';

const configPath = process.argv[2] ?? 'calibration-config.json';
const bankPath = process.argv[3] ?? 'tests/core.yaml';
const outPath = process.argv[4] ?? 'tests/sol-calibration-selected.yaml';

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const plan = config.solExploration ?? {};
const language = String(plan.language ?? 'en').trim();
const pairIds = Array.isArray(plan.pairIds) ? plan.pairIds : [];

if (!['en', 'zh'].includes(language)) {
  throw new Error('solExploration.language must be en or zh');
}
if (!pairIds.length) {
  throw new Error('solExploration.pairIds must not be empty');
}
if (new Set(pairIds).size !== pairIds.length) {
  throw new Error('solExploration.pairIds contains duplicates');
}

const source = fs.readFileSync(bankPath, 'utf8');
const starts = [...source.matchAll(/^- description:/gm)].map((m) => m.index);
const byKey = new Map();

for (let i = 0; i < starts.length; i += 1) {
  const start = starts[i];
  const end = i + 1 < starts.length ? starts[i + 1] : source.length;
  let block = source.slice(start, end).trimEnd();
  block = block.replace(/\n# --------------------[\s\S]*$/m, '').trimEnd();

  const pairId = block.match(/^\s+pair_id:\s*(\S+)/m)?.[1]?.trim();
  const lang = block.match(/^\s+language:\s*(\S+)/m)?.[1]?.trim();
  if (pairId && lang) byKey.set(`${pairId}|${lang}`, block);
}

const blocks = [];
for (const pairId of pairIds) {
  const block = byKey.get(`${pairId}|${language}`);
  if (!block) throw new Error(`Missing ${language} version for ${pairId}`);
  blocks.push(block);
}

const header = [
  '# AUTO-GENERATED calibration subset. Do not edit.',
  `# Language: ${language}`,
  `# Pair IDs: ${pairIds.join(', ')}`,
  '',
].join('\n');

fs.writeFileSync(outPath, header + blocks.join('\n\n') + '\n');
console.log(`Calibration subset: ${pairIds.length} questions, language=${language}`);
console.log(`Pair IDs: ${pairIds.join(', ')}`);
