import fs from 'node:fs';
import crypto from 'node:crypto';

const configPath = process.argv[2] ?? 'monitor-config.json';
const bankPath = process.argv[3] ?? 'tests/core.yaml';
const metadataPath = process.argv[4] ?? 'tests/question-metadata.json';
const outTests = process.argv[5] ?? 'tests/selected.yaml';
const outSelection = process.argv[6] ?? 'results/selection.json';

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
const source = fs.readFileSync(bankPath, 'utf8');

function intOverride(name, fallback) {
  const raw = process.env[name];
  if (raw == null || raw.trim() === '') return fallback;
  const value = Number.parseInt(raw, 10);
  if (!Number.isInteger(value) || value < 0) {
    throw new Error(`${name} must be a non-negative integer`);
  }
  return value;
}

function getRunDate() {
  const supplied = process.env.RUN_DATE?.trim();
  if (supplied) return supplied;
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date());
}

function parseEntries(text) {
  const starts = [...text.matchAll(/^- description:/gm)].map((m) => m.index);
  const entries = [];
  for (let i = 0; i < starts.length; i += 1) {
    const start = starts[i];
    const end = i + 1 < starts.length ? starts[i + 1] : text.length;
    let block = text.slice(start, end).trimEnd();
    // Section dividers belong to the following group semantically, not the
    // preceding question. Removing them keeps generated YAML compact.
    block = block.replace(/\n# --------------------[\s\S]*$/m, '').trimEnd();

    const description = block.match(/^- description:\s*(.+)$/m)?.[1]?.trim();
    const pairId = block.match(/^\s+pair_id:\s*(\S+)/m)?.[1]?.trim();
    const language = block.match(/^\s+language:\s*(\S+)/m)?.[1]?.trim();
    const category = block.match(/^\s+category:\s*(\S+)/m)?.[1]?.trim();
    const answer = block.match(/^\s+value:\s*(.+)$/m)?.[1]?.trim();

    if (!description || !pairId || !language) {
      throw new Error(`Cannot parse question entry near: ${block.slice(0, 120)}`);
    }
    entries.push({ description, pairId, language, category, answer, block });
  }
  return entries;
}

function stableHash(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function allocateQuotas(total, weights) {
  const items = Object.entries(weights);
  const weightSum = items.reduce((sum, [, w]) => sum + Number(w), 0);
  if (weightSum <= 0) throw new Error('rotatingDifficultyWeights must have positive total weight');

  const quotas = {};
  const remainders = [];
  let assigned = 0;

  items.forEach(([name, weight], index) => {
    const exact = total * Number(weight) / weightSum;
    const base = Math.floor(exact);
    quotas[name] = base;
    assigned += base;
    remainders.push({ name, remainder: exact - base, index });
  });

  remainders.sort((a, b) => b.remainder - a.remainder || a.index - b.index);
  for (let i = 0; i < total - assigned; i += 1) {
    quotas[remainders[i % remainders.length].name] += 1;
  }
  return quotas;
}

const entries = parseEntries(source);
const pairs = new Map();
for (const entry of entries) {
  if (!pairs.has(entry.pairId)) pairs.set(entry.pairId, {});
  const pair = pairs.get(entry.pairId);
  if (pair[entry.language]) {
    throw new Error(`Duplicate language ${entry.language} for ${entry.pairId}`);
  }
  pair[entry.language] = entry;
}

for (const [pairId, pair] of pairs) {
  if (!pair.zh || !pair.en) throw new Error(`${pairId} does not have both zh and en versions`);
  if (pair.zh.answer !== pair.en.answer) {
    throw new Error(`${pairId} Chinese/English expected answers differ: ${pair.zh.answer} vs ${pair.en.answer}`);
  }
  if (!metadata[pairId]) throw new Error(`Missing metadata for ${pairId}`);
}
for (const pairId of Object.keys(metadata)) {
  if (!pairs.has(pairId)) throw new Error(`Metadata references missing pair ${pairId}`);
}

const daily = config.daily ?? {};
const anchorCount = intOverride('ANCHOR_COUNT_OVERRIDE', daily.anchorCount ?? 6);
const rotatingCount = intOverride('ROTATING_COUNT_OVERRIDE', daily.rotatingCount ?? 6);
const repeat = intOverride('REPEAT_OVERRIDE', daily.repeat ?? 1);
const runDate = getRunDate();
const anchorPool = daily.anchorPool ?? [];

if (anchorCount > anchorPool.length) {
  throw new Error(`anchorCount=${anchorCount} exceeds anchorPool size=${anchorPool.length}`);
}

const anchorIds = anchorPool.slice(0, anchorCount);
for (const id of anchorIds) {
  if (!pairs.has(id)) throw new Error(`Anchor ${id} is not in the question bank`);
}

const selectedSet = new Set(anchorIds);
const abilityCounts = {};
const difficultyCounts = {};
for (const id of anchorIds) {
  const m = metadata[id];
  abilityCounts[m.ability] = (abilityCounts[m.ability] ?? 0) + 1;
  difficultyCounts[m.difficulty] = (difficultyCounts[m.difficulty] ?? 0) + 1;
}

const quotas = allocateQuotas(rotatingCount, daily.rotatingDifficultyWeights ?? { standard: 1, hard: 1, extreme: 2, ultra: 2 });
const rotatingIds = [];

for (const [difficulty, quota] of Object.entries(quotas)) {
  for (let slot = 0; slot < quota; slot += 1) {
    const candidates = [...pairs.keys()].filter((id) =>
      !selectedSet.has(id) && metadata[id]?.difficulty === difficulty
    );

    if (!candidates.length) {
      throw new Error(`Not enough unused questions for difficulty=${difficulty}; requested quota=${quota}`);
    }

    candidates.sort((a, b) => {
      const ac = abilityCounts[metadata[a].ability] ?? 0;
      const bc = abilityCounts[metadata[b].ability] ?? 0;
      if (ac !== bc) return ac - bc;
      return stableHash(`${runDate}|${difficulty}|${a}`).localeCompare(
        stableHash(`${runDate}|${difficulty}|${b}`)
      );
    });

    const chosen = candidates[0];
    rotatingIds.push(chosen);
    selectedSet.add(chosen);
    const m = metadata[chosen];
    abilityCounts[m.ability] = (abilityCounts[m.ability] ?? 0) + 1;
    difficultyCounts[m.difficulty] = (difficultyCounts[m.difficulty] ?? 0) + 1;
  }
}

const selectedIds = [...anchorIds, ...rotatingIds];
const outBlocks = [];
for (const id of selectedIds) {
  const pair = pairs.get(id);
  // Always keep the two language mirrors together.
  outBlocks.push(pair.zh.block, pair.en.block);
}

fs.mkdirSync('results', { recursive: true });
fs.writeFileSync(
  outTests,
  [
    '# AUTO-GENERATED. Do not edit.',
    `# Daily selection date (Asia/Shanghai): ${runDate}`,
    `# ${anchorCount} fixed anchors + ${rotatingCount} rotating canonical questions = ${selectedIds.length * 2} bilingual tests.`,
    '',
    ...outBlocks,
    '',
  ].join('\n\n'),
);

const selection = {
  mode: 'daily',
  runDate,
  repeat,
  bankCanonicalQuestions: pairs.size,
  anchorCount,
  rotatingCount,
  canonicalQuestionsSelected: selectedIds.length,
  bilingualTestsSelected: selectedIds.length * 2,
  anchors: anchorIds,
  rotating: rotatingIds,
  selected: selectedIds.map((id) => ({
    pairId: id,
    ...metadata[id],
  })),
  distribution: {
    ability: abilityCounts,
    difficulty: difficultyCounts,
    rotatingDifficultyQuota: quotas,
  },
  deepTestEnabled: Boolean(config.deepTest?.enabled),
};

fs.writeFileSync(outSelection, JSON.stringify(selection, null, 2) + '\n');

console.log(`Daily selection for ${runDate}: ${anchorCount} anchors + ${rotatingCount} rotating = ${selectedIds.length} canonical questions / ${selectedIds.length * 2} bilingual tests`);
console.log(`Anchors: ${anchorIds.join(', ')}`);
console.log(`Rotating: ${rotatingIds.join(', ')}`);
console.log(`Difficulty: ${JSON.stringify(difficultyCounts)}`);
console.log(`Ability: ${JSON.stringify(abilityCounts)}`);
