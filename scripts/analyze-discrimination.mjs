import fs from 'node:fs';

const input = process.argv[2] ?? 'results/combined-results.json';
const outJson = process.argv[3] ?? 'results/discrimination.json';
const outMd = process.argv[4] ?? 'results/discrimination.md';
const metadataPath = process.argv[5] ?? 'tests/question-metadata.json';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
const rows = data?.results?.results ?? data?.results?.outputs ?? data?.results ?? [];
if (!Array.isArray(rows)) throw new Error('Unable to locate Promptfoo result rows.');

const efforts = ['medium', 'high', 'xhigh'];
const effortLabel = { medium: 'Medium', high: 'High', xhigh: 'X High' };

const num = (v) => Number.isFinite(v) ? v : 0;
const errorText = (row) => {
  const value = row?.error ?? row?.response?.error;
  if (!value) return '';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value); } catch { return String(value); }
};
const failureReason = (row) => Number(row?.failureReason ?? 0);
const isTimeout = (row) =>
  failureReason(row) === 2 &&
  /timeout|timed out|600000ms|deadline exceeded/i.test(errorText(row));
const isApiError = (row) =>
  !row?.success && failureReason(row) === 2 && !isTimeout(row);

function parseEffort(provider) {
  const text = String(provider ?? '');
  if (/X High/i.test(text)) return 'xhigh';
  if (/\bHigh\b/i.test(text)) return 'high';
  if (/\bMedium\b/i.test(text)) return 'medium';
  return null;
}

function fresh() {
  return {
    total: 0,
    passed: 0,
    wrong: 0,
    timeouts: 0,
    apiErrors: 0,
    reasoningTokens: 0,
    totalTokens: 0,
    latencyMs: 0,
    validLatencyCount: 0,
    zh: { total: 0, passed: 0 },
    en: { total: 0, passed: 0 },
  };
}

function add(s, row, language) {
  s.total += 1;
  if (row?.success) s.passed += 1;
  else if (isTimeout(row)) s.timeouts += 1;
  else if (isApiError(row)) s.apiErrors += 1;
  else s.wrong += 1;

  if (language === 'zh' || language === 'en') {
    s[language].total += 1;
    if (row?.success) s[language].passed += 1;
  }

  const u = row?.tokenUsage ?? row?.response?.tokenUsage ?? {};
  s.reasoningTokens += num(u?.completionDetails?.reasoning);
  s.totalTokens += num(u.total);

  if (!isTimeout(row) && !isApiError(row) && Number.isFinite(row?.latencyMs)) {
    s.latencyMs += row.latencyMs;
    s.validLatencyCount += 1;
  }
}

function finish(s) {
  return {
    ...s,
    passRate: s.total ? s.passed / s.total : null,
    averageReasoningTokens: s.total ? s.reasoningTokens / s.total : null,
    averageTotalTokens: s.total ? s.totalTokens / s.total : null,
    averageLatencyMs: s.validLatencyCount ? s.latencyMs / s.validLatencyCount : null,
    zhPassRate: s.zh.total ? s.zh.passed / s.zh.total : null,
    enPassRate: s.en.total ? s.en.passed / s.en.total : null,
  };
}

const overall = Object.fromEntries(efforts.map((e) => [e, fresh()]));
const pairs = new Map();

for (const row of rows) {
  const provider =
    row?.provider?.label ??
    row?.provider?.id ??
    row?.provider ??
    '';
  const effort = parseEffort(provider);
  if (!effort) continue;

  const vars = row?.vars ?? row?.testCase?.vars ?? {};
  const pairId = vars.pair_id ?? 'unknown';
  const language = vars.language ?? 'unknown';

  add(overall[effort], row, language);

  if (!pairs.has(pairId)) {
    pairs.set(pairId, {
      pairId,
      ability: metadata[pairId]?.ability ?? 'unknown',
      difficulty: metadata[pairId]?.difficulty ?? 'unknown',
      dailyEligible: metadata[pairId]?.dailyEligible !== false,
      efforts: Object.fromEntries(efforts.map((e) => [e, fresh()])),
    });
  }
  add(pairs.get(pairId).efforts[effort], row, language);
}

const results = [...pairs.values()].map((p) => {
  const e = Object.fromEntries(efforts.map((name) => [name, finish(p.efforts[name])]));
  const rates = efforts.map((name) => e[name].passRate ?? 0);
  const medium = e.medium.passRate ?? 0;
  const high = e.high.passRate ?? 0;
  const xhigh = e.xhigh.passRate ?? 0;
  const maxRate = Math.max(...rates);
  const minRate = Math.min(...rates);
  const span = maxRate - minRate;
  const effortGain = xhigh - medium;
  const monotonic = medium <= high && high <= xhigh;

  let classification = 'low-signal';
  let recommendation = 'keep-for-model-comparison-only';

  if (minRate >= 0.99) {
    classification = 'ceiling';
    recommendation = 'replace-or-downgrade-weight';
  } else if (maxRate <= 0.01) {
    classification = 'floor';
    recommendation = 'simplify-or-replace';
  } else if (monotonic && effortGain >= 0.5) {
    classification = 'effort-discriminator';
    recommendation = 'promote-to-effort-anchor';
  } else if (effortGain >= 0.5) {
    classification = 'effort-candidate';
    recommendation = 'repeat-before-promoting';
  } else if (
    high + 0.5 <= medium ||
    xhigh + 0.5 <= high ||
    xhigh + 0.5 <= medium
  ) {
    classification = 'non-monotonic';
    recommendation = 'repeat-and-inspect';
  } else if (span >= 0.5) {
    classification = 'variable';
    recommendation = 'repeat-and-inspect';
  }

  const informationScore =
    Math.max(0, effortGain) * 2 +
    span +
    (monotonic ? 0.25 : 0) -
    (classification === 'ceiling' || classification === 'floor' ? 1 : 0);

  return {
    pairId: p.pairId,
    ability: p.ability,
    difficulty: p.difficulty,
    dailyEligible: p.dailyEligible,
    efforts: e,
    mediumPassRate: medium,
    highPassRate: high,
    xhighPassRate: xhigh,
    effortGain,
    span,
    monotonic,
    classification,
    recommendation,
    informationScore,
  };
});

results.sort((a, b) =>
  b.informationScore - a.informationScore ||
  b.effortGain - a.effortGain ||
  a.pairId.localeCompare(b.pairId)
);

const finishedOverall = Object.fromEntries(
  efforts.map((e) => [e, finish(overall[e])])
);

const counts = {};
for (const r of results) counts[r.classification] = (counts[r.classification] ?? 0) + 1;

const output = {
  generatedAt: new Date().toISOString(),
  mode: 'gpt-6-sol-effort-calibration',
  note: 'Exploratory pass. Each canonical problem has only its zh/en mirrors at each effort, so classifications are provisional until repeated.',
  overall: finishedOverall,
  classificationCounts: counts,
  questions: results,
};

fs.mkdirSync('results', { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const pct = (v) => v == null ? '-' : `${(v * 100).toFixed(0)}%`;
const n = (v, digits = 0) =>
  v == null ? '-' : Number(v).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
const latency = (v) => v == null ? '-' : `${(v / 1000).toFixed(1)}s`;

const lines = [
  '# GPT-6 Sol 思考档位区分度校准',
  '',
  '> 本轮只用于前期探索。每道原始题在每个档位目前只有中英文两个样本，因此逐题分类是候选结论，不直接作为最终定级。',
  '',
  '## 总体',
  '',
  '| 档位 | 正确率 | Reasoning Token/题 | 总 Token/题 | 平均响应时间 |',
  '|---|---:|---:|---:|---:|',
];

for (const e of efforts) {
  const s = finishedOverall[e];
  lines.push(
    `| ${effortLabel[e]} | ${s.passed}/${s.total}（${pct(s.passRate)}） | ${n(s.averageReasoningTokens, 1)} | ${n(s.averageTotalTokens, 1)} | ${latency(s.averageLatencyMs)} |`
  );
}

lines.push(
  '',
  '## 初步分类',
  '',
  ...Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `- ${k}: ${v}`),
  '',
  '## 逐题区分度',
  '',
  '| 题目 | 能力 | 难度 | Medium | High | X High | XH-M | 单调 | 分类 | 建议 |',
  '|---|---|---|---:|---:|---:|---:|:---:|---|---|',
);

for (const r of results) {
  lines.push(
    `| ${r.pairId} | ${r.ability} | ${r.difficulty} | ${pct(r.mediumPassRate)} | ${pct(r.highPassRate)} | ${pct(r.xhighPassRate)} | ${(r.effortGain * 100).toFixed(0)}pp | ${r.monotonic ? '是' : '否'} | ${r.classification} | ${r.recommendation} |`
  );
}

const best = results.filter((r) =>
  r.classification === 'effort-discriminator' ||
  r.classification === 'effort-candidate'
);
const ceiling = results.filter((r) => r.classification === 'ceiling');
const noisy = results.filter((r) =>
  r.classification === 'non-monotonic' ||
  r.classification === 'variable'
);

lines.push(
  '',
  '## 下一轮建议',
  '',
  `- 档位区分候选：${best.length ? best.map((x) => x.pairId).join(', ') : '暂无'}。下一轮优先 repeat=3 复测这些题。`,
  `- 封顶题：${ceiling.length ? ceiling.map((x) => x.pairId).join(', ') : '暂无'}。若目标是区分强模型/高档位，应降低权重或替换。`,
  `- 非单调/波动题：${noisy.length ? noisy.map((x) => x.pairId).join(', ') : '暂无'}。先复测，不要直接判定档位关系。`,
  '- 只有在 Sol 的题型和难度阈值相对稳定后，再启动四模型全量验证。',
  ''
);

fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
