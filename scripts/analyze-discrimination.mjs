import fs from 'node:fs';

const input = process.argv[2] ?? 'results/combined-results.json';
const outJson = process.argv[3] ?? 'results/discrimination.json';
const outMd = process.argv[4] ?? 'results/discrimination.md';
const metadataPath = process.argv[5] ?? 'tests/question-metadata.json';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
const rows = data?.results?.results ?? data?.results?.outputs ?? data?.results ?? [];
if (!Array.isArray(rows)) throw new Error('Unable to locate Promptfoo result rows.');

const effortOrder = ['medium', 'high', 'xhigh'];
const effortLabel = { medium: 'Medium', high: 'High', xhigh: 'X High' };
const minRepeatSamples = 3;
const strongGain = 0.6;
const candidateGain = 0.10;

function parseEffort(provider) {
  const text = String(provider ?? '');
  if (/X[ _-]?High/i.test(text) || /\bxhigh\b/i.test(text)) return 'xhigh';
  if (/\bhigh\b/i.test(text)) return 'high';
  if (/\bmedium\b/i.test(text)) return 'medium';
  return null;
}

const availableEfforts = effortOrder.filter((effort) =>
  rows.some((row) => {
    const provider = row?.provider?.label ?? row?.provider?.id ?? row?.provider ?? '';
    return parseEffort(provider) === effort;
  })
);

if (!availableEfforts.length) throw new Error('No recognizable reasoning effort labels found.');

const num = (v) => Number.isFinite(v) ? v : 0;
const failureReason = (row) => Number(row?.failureReason ?? 0);
const errorText = (row) => {
  const value = row?.error ?? row?.response?.error;
  if (!value) return '';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value); } catch { return String(value); }
};
const isTimeout = (row) =>
  failureReason(row) === 2 &&
  /timeout|timed out|600000ms|deadline exceeded/i.test(errorText(row));
const isApiError = (row) =>
  !row?.success && failureReason(row) === 2 && !isTimeout(row);

function fresh() {
  return {
    total: 0, passed: 0, wrong: 0, timeouts: 0, apiErrors: 0,
    reasoningTokens: 0, totalTokens: 0, latencyMs: 0, validLatencyCount: 0,
    scoreSum: 0, scoreSqSum: 0, validScoreCount: 0,
  };
}

function add(s, row) {
  s.total += 1;
  if (row?.success) s.passed += 1;
  else if (isTimeout(row)) s.timeouts += 1;
  else if (isApiError(row)) s.apiErrors += 1;
  else s.wrong += 1;

  const rawScore = Number.isFinite(Number(row?.score))
    ? Number(row.score)
    : (Number.isFinite(Number(row?.gradingResult?.score)) ? Number(row.gradingResult.score) : null);
  if (rawScore != null && !isApiError(row) && !isTimeout(row)) {
    const score = Math.max(0, Math.min(1, rawScore));
    s.scoreSum += score;
    s.scoreSqSum += score * score;
    s.validScoreCount += 1;
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
  const averageScore = s.validScoreCount ? s.scoreSum / s.validScoreCount : null;
  const scoreVariance = s.validScoreCount
    ? Math.max(0, s.scoreSqSum / s.validScoreCount - averageScore * averageScore)
    : null;
  return {
    total: s.total,
    passed: s.passed,
    wrong: s.wrong,
    timeouts: s.timeouts,
    apiErrors: s.apiErrors,
    passRate: s.total ? s.passed / s.total : null,
    averageScore,
    scoreStddev: scoreVariance == null ? null : Math.sqrt(scoreVariance),
    scoreSamples: s.validScoreCount,
    averageReasoningTokens: s.total ? s.reasoningTokens / s.total : null,
    averageTotalTokens: s.total ? s.totalTokens / s.total : null,
    averageLatencyMs: s.validLatencyCount ? s.latencyMs / s.validLatencyCount : null,
  };
}

const overall = Object.fromEntries(availableEfforts.map((e) => [e, fresh()]));
const pairs = new Map();

for (const row of rows) {
  const provider = row?.provider?.label ?? row?.provider?.id ?? row?.provider ?? '';
  const effort = parseEffort(provider);
  if (!availableEfforts.includes(effort)) continue;

  const vars = row?.vars ?? row?.testCase?.vars ?? {};
  const pairId = vars.pair_id ?? 'unknown';

  add(overall[effort], row);

  if (!pairs.has(pairId)) {
    pairs.set(pairId, {
      pairId,
      ability: metadata[pairId]?.ability ?? vars.ability ?? vars.category ?? 'unknown',
      difficulty: metadata[pairId]?.difficulty ?? vars.difficulty ?? 'research',
      efforts: Object.fromEntries(availableEfforts.map((e) => [e, fresh()])),
    });
  }
  add(pairs.get(pairId).efforts[effort], row);
}

const results = [...pairs.values()].map((p) => {
  const efforts = Object.fromEntries(
    availableEfforts.map((e) => [e, finish(p.efforts[e])])
  );

  const metricFor = (effort) => {
    const x = efforts[effort];
    if (!x) return null;
    return x.averageScore ?? x.passRate ?? null;
  };
  const medium = metricFor('medium');
  const high = metricFor('high');
  const xhigh = metricFor('xhigh');
  const rates = availableEfforts
    .map(metricFor)
    .filter((v) => v != null);

  let classification = 'needs-more-data';
  let recommendation = 'inspect';
  let effortGain = null;
  let repeatedEnough = false;
  let monotonic = null;

  if (medium != null && xhigh != null) {
    effortGain = xhigh - medium;
    const mediumN = efforts.medium?.total ?? 0;
    const xhighN = efforts.xhigh?.total ?? 0;
    repeatedEnough = Math.min(mediumN, xhighN) >= minRepeatSamples;

    if (high != null) {
      monotonic = medium <= high && high <= xhigh
        ? 'nondecreasing'
        : (medium >= high && high >= xhigh ? 'nonincreasing' : 'nonmonotonic');
    }

    if (medium >= 0.95 && xhigh >= 0.95) {
      classification = 'ceiling';
      recommendation = 'drop-from-effort-calibration';
    } else if (medium <= 0.05 && xhigh <= 0.05) {
      classification = 'floor';
      recommendation = 'simplify-or-replace';
    } else if (!repeatedEnough && Math.abs(effortGain) > 0) {
      classification = effortGain > 0 ? 'one-shot-effort-candidate' : 'one-shot-reverse-candidate';
      recommendation = 'repeat-before-using';
    } else if (effortGain >= strongGain) {
      classification = 'strong-effort-signal';
      recommendation = high == null ? 'test-high' : 'validate-family';
    } else if (effortGain >= candidateGain) {
      classification = 'effort-candidate';
      recommendation = high == null ? 'test-high' : 'repeat-family';
    } else if (effortGain <= -candidateGain) {
      classification = 'reverse-signal';
      recommendation = 'repeat-before-using';
    } else if (Math.abs(effortGain) < 1e-9) {
      classification = 'same-outcome';
      recommendation = 'low-priority';
    } else {
      classification = 'weak-difference';
      recommendation = 'low-priority';
    }
  }

  const span = rates.length ? Math.max(...rates) - Math.min(...rates) : 0;

  return {
    pairId: p.pairId,
    ability: p.ability,
    difficulty: p.difficulty,
    efforts,
    mediumPassRate: efforts.medium?.passRate ?? null,
    highPassRate: efforts.high?.passRate ?? null,
    xhighPassRate: efforts.xhigh?.passRate ?? null,
    mediumScore: medium,
    highScore: high,
    xhighScore: xhigh,
    effortGain,
    span,
    repeatedEnough,
    monotonic,
    classification,
    recommendation,
  };
});

const priority = {
  'strong-effort-signal': 0,
  'effort-candidate': 1,
  'one-shot-effort-candidate': 2,
  'reverse-signal': 3,
  'one-shot-reverse-candidate': 4,
  'weak-difference': 5,
  'floor': 6,
  'same-outcome': 7,
  'ceiling': 8,
  'needs-more-data': 9,
};
results.sort((a, b) =>
  (priority[a.classification] ?? 99) - (priority[b.classification] ?? 99) ||
  a.pairId.localeCompare(b.pairId)
);

const output = {
  generatedAt: new Date().toISOString(),
  mode: 'gpt-6-sol-effort-calibration',
  exploratory: true,
  availableEfforts,
  overall: Object.fromEntries(availableEfforts.map((e) => [e, finish(overall[e])])),
  questions: results,
};

fs.mkdirSync('results', { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const pct = (v) => v == null ? '-' : `${(v * 100).toFixed(0)}%`;
const fmt = (v, digits = 0) => v == null ? '-' : Number(v).toLocaleString('en-US', {
  minimumFractionDigits: digits,
  maximumFractionDigits: digits,
});
const latency = (v) => v == null ? '-' : `${(v / 1000).toFixed(1)}s`;

const lines = [
  '# GPT-6 Sol 思考档位低成本校准',
  '',
  `> 这是探索性筛选，不是最终定级。优先使用 Promptfoo 客观 assertion score（0–1），没有部分分数时才退回 pass/fail。正式 effort 候选至少需要 ${minRepeatSamples} 个重复样本且 Medium→X High 平均客观分提升至少 10pp；单次分差只记为 one-shot candidate。`,
  '',
  '## 总体',
  '',
  '| 档位 | 正确率 | 平均客观分 | 平均 Reasoning Token | 平均总 Token | 平均响应时间 |',
  '|---|---:|---:|---:|---:|---:|',
];

for (const effort of availableEfforts) {
  const s = output.overall[effort];
  lines.push(
    `| ${effortLabel[effort]} | ${s.passed}/${s.total}（${pct(s.passRate)}） | ${pct(s.averageScore)} | ${fmt(s.averageReasoningTokens, 1)} | ${fmt(s.averageTotalTokens, 1)} | ${latency(s.averageLatencyMs)} |`
  );
}

lines.push(
  '',
  '## 逐题',
  '',
  '| 题目 | 能力 | 难度 | Medium 分 | High 分 | X High 分 | XH-M | M/H/XH 通过率 | 重复充分 | 形状 | 分类 | 下一步 |',
  '|---|---|---|---:|---:|---:|---:|---|:---:|---|---|---|',
);

for (const r of results) {
  lines.push(
    `| ${r.pairId} | ${r.ability} | ${r.difficulty} | ${pct(r.mediumScore)} | ${pct(r.highScore)} | ${pct(r.xhighScore)} | ${r.effortGain == null ? '-' : (r.effortGain * 100).toFixed(0) + 'pp'} | ${pct(r.mediumPassRate)}/${pct(r.highPassRate)}/${pct(r.xhighPassRate)} | ${r.repeatedEnough ? '是' : '否'} | ${r.monotonic ?? '-'} | ${r.classification} | ${r.recommendation} |`
  );
}

const candidates = results.filter((r) =>
  r.classification === 'strong-effort-signal' ||
  r.classification === 'effort-candidate'
);
lines.push(
  '',
  '## 下一步',
  '',
  `- 候选题：${candidates.length ? candidates.map((x) => x.pairId).join(', ') : '暂无'}。`,
  '- 下一轮只对候选题做重复验证；确认稳定后才补跑 High。',
  '- 题型和阈值稳定后，再进行四模型全量验证。',
  ''
);

fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
