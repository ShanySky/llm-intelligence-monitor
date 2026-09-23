import fs from 'node:fs';

const input = process.argv[2] ?? 'results/results.json';
const outJson = process.argv[3] ?? 'results/summary.json';
const outMd = process.argv[4] ?? 'results/summary.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const selectionPath = 'results/selection.json';
const selection = fs.existsSync(selectionPath)
  ? JSON.parse(fs.readFileSync(selectionPath, 'utf8'))
  : null;

const rows = data?.results?.results ?? data?.results?.outputs ?? data?.results ?? [];
if (!Array.isArray(rows)) throw new Error('Unable to locate Promptfoo result rows.');

const anchorSet = new Set(selection?.anchors ?? []);
const rotatingSet = new Set(selection?.rotating ?? []);

const num = (v) => Number.isFinite(v) ? v : 0;
const errorText = (row) => {
  const value = row?.error ?? row?.response?.error;
  if (!value) return '';
  if (typeof value === 'string') return value;
  try { return JSON.stringify(value); } catch { return String(value); }
};
const failureReason = (row) => Number(row?.failureReason ?? 0);
const isTimeoutRow = (row) =>
  failureReason(row) === 2 &&
  /timeout|timed out|600000ms|deadline exceeded/i.test(errorText(row));
const isExecutionError = (row) =>
  !row?.success && failureReason(row) === 2 && !isTimeoutRow(row);

const freshStats = () => ({
  total: 0,
  passed: 0,
  wrong: 0,
  timeouts: 0,
  apiErrors: 0,
  scoreSum: 0,
  validLatencySum: 0,
  validLatencyCount: 0,
  costUsd: 0,
  tokenUsage: {
    prompt: 0,
    completion: 0,
    reasoning: 0,
    cached: 0,
    total: 0,
    numRequests: 0,
  },
  validTokenUsage: {
    prompt: 0,
    completion: 0,
    reasoning: 0,
    cached: 0,
    total: 0,
    numRequests: 0,
  },
});

const addRow = (s, row) => {
  s.total += 1;

  const reason = failureReason(row);
  const timeout = isTimeoutRow(row);
  const executionError = isExecutionError(row);

  if (row?.success) s.passed += 1;
  else if (reason === 1) s.wrong += 1;
  else if (timeout) s.timeouts += 1;
  else if (executionError) s.apiErrors += 1;
  // Fallback for providers/versions that do not populate failureReason.
  else if (/^Expected output /i.test(errorText(row))) s.wrong += 1;
  else if (errorText(row)) s.apiErrors += 1;
  else s.wrong += 1;

  s.scoreSum += num(row?.score);

  // Do not let timeout/API-error wall time pollute normal response-time baselines.
  if (!timeout && !executionError && Number.isFinite(row?.latencyMs)) {
    s.validLatencySum += row.latencyMs;
    s.validLatencyCount += 1;
  }

  s.costUsd += num(row?.cost ?? row?.response?.cost);

  const u = row?.tokenUsage ?? row?.response?.tokenUsage ?? {};
  s.tokenUsage.prompt += num(u.prompt);
  s.tokenUsage.completion += num(u.completion);
  s.tokenUsage.cached += num(u.cached);
  s.tokenUsage.total += num(u.total);
  s.tokenUsage.numRequests += num(u.numRequests) || 1;
  s.tokenUsage.reasoning += num(u?.completionDetails?.reasoning);

  if (!timeout && !executionError) {
    s.validTokenUsage.prompt += num(u.prompt);
    s.validTokenUsage.completion += num(u.completion);
    s.validTokenUsage.cached += num(u.cached);
    s.validTokenUsage.total += num(u.total);
    s.validTokenUsage.numRequests += num(u.numRequests) || 1;
    s.validTokenUsage.reasoning += num(u?.completionDetails?.reasoning);
  }
};

const finish = (s) => {
  const answered = s.passed + s.wrong;
  const tokenDivisor = answered || 1;

  return {
    total: s.total,
    passed: s.passed,
    wrong: s.wrong,
    timeouts: s.timeouts,
    apiErrors: s.apiErrors,
    answered,
    unfinished: s.timeouts + s.apiErrors,
    passRate: s.total ? s.passed / s.total : 0,
    answeredPassRate: answered ? s.passed / answered : 0,
    timeoutRate: s.total ? s.timeouts / s.total : 0,
    apiErrorRate: s.total ? s.apiErrors / s.total : 0,
    averageScore: s.total ? s.scoreSum / s.total : 0,
    averageLatencyMs: s.validLatencyCount ? s.validLatencySum / s.validLatencyCount : null,
    estimatedCostUsd: s.costUsd,
    tokenUsage: s.tokenUsage,
    averageTokens: {
      prompt: s.validTokenUsage.prompt / tokenDivisor,
      completion: s.validTokenUsage.completion / tokenDivisor,
      reasoning: s.validTokenUsage.reasoning / tokenDivisor,
      cached: s.validTokenUsage.cached / tokenDivisor,
      total: s.validTokenUsage.total / tokenDivisor,
    },
  };
};

const buckets = new Map();
const bucketFor = (name) => {
  if (!buckets.has(name)) {
    buckets.set(name, {
      provider: name,
      overall: freshStats(),
      anchor: freshStats(),
      rotating: freshStats(),
      languages: { zh: freshStats(), en: freshStats() },
      categories: {},
      pairs: {},
    });
  }
  return buckets.get(name);
};

for (const row of rows) {
  const provider =
    row?.provider?.label ??
    row?.provider?.id ??
    row?.provider ??
    '未知模型';

  const vars = row?.vars ?? row?.testCase?.vars ?? {};
  const category = vars.category ?? 'uncategorized';
  const language = vars.language ?? 'unknown';
  const pairId = vars.pair_id ?? 'unknown';

  const b = bucketFor(provider);
  addRow(b.overall, row);
  if (anchorSet.has(pairId)) addRow(b.anchor, row);
  if (rotatingSet.has(pairId)) addRow(b.rotating, row);
  if (b.languages[language]) addRow(b.languages[language], row);

  if (!b.categories[category]) {
    b.categories[category] = {
      all: freshStats(),
      zh: freshStats(),
      en: freshStats(),
    };
  }
  addRow(b.categories[category].all, row);
  if (b.categories[category][language]) addRow(b.categories[category][language], row);

  if (!b.pairs[pairId]) b.pairs[pairId] = { zh: freshStats(), en: freshStats() };
  if (b.pairs[pairId][language]) addRow(b.pairs[pairId][language], row);
}

const providers = [...buckets.values()].map((b) => {
  const pairComparison = {
    zhBetter: 0,
    enBetter: 0,
    equal: 0,
    comparablePairs: 0,
    disagreementPairs: [],
  };

  for (const [pairId, p] of Object.entries(b.pairs)) {
    const zh = finish(p.zh);
    const en = finish(p.en);
    if (!zh.answered || !en.answered) continue;

    pairComparison.comparablePairs += 1;
    const zr = zh.answeredPassRate;
    const er = en.answeredPassRate;

    if (zr > er) {
      pairComparison.zhBetter += 1;
      pairComparison.disagreementPairs.push({ pairId, better: 'zh', zhPassRate: zr, enPassRate: er });
    } else if (er > zr) {
      pairComparison.enBetter += 1;
      pairComparison.disagreementPairs.push({ pairId, better: 'en', zhPassRate: zr, enPassRate: er });
    } else {
      pairComparison.equal += 1;
    }
  }

  return {
    provider: b.provider,
    overall: finish(b.overall),
    anchor: finish(b.anchor),
    rotating: finish(b.rotating),
    languages: { zh: finish(b.languages.zh), en: finish(b.languages.en) },
    languageGapPctPoints:
      (b.languages.zh.total ? finish(b.languages.zh).answeredPassRate : 0) * 100 -
      (b.languages.en.total ? finish(b.languages.en).answeredPassRate : 0) * 100,
    pairComparison,
    categories: Object.fromEntries(
      Object.entries(b.categories).map(([name, c]) => [
        name,
        { all: finish(c.all), zh: finish(c.zh), en: finish(c.en) },
      ]),
    ),
  };
});

const summary = {
  generatedAt: new Date().toISOString(),
  evalTimestamp: data?.timestamp ?? data?.results?.timestamp ?? null,
  evalId: data?.evalId ?? data?.results?.evalId ?? null,
  selection,
  providers,
};

fs.mkdirSync(new URL('../results/', import.meta.url), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(summary, null, 2) + '\n');

const fmt = (n, digits = 0) =>
  Number(n ?? 0).toLocaleString('en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
const pct = (r) => `${(Number(r ?? 0) * 100).toFixed(1)}%`;
const latency = (v) => v == null ? '无' : `${fmt(v / 1000, 2)} 秒`;

const categoryName = {
  reasoning: '推理',
  math: '数学',
  coding: '代码',
  instruction: '指令遵循',
  stress: '压力题',
  extreme: '极限题',
  ultra: '超高难题',
  uncategorized: '未分类',
};

const difficultyName = { standard: '标准', hard: '困难', extreme: '极限', ultra: '超高难' };
const abilityName = { reasoning: '推理', math: '数学', coding: '代码', instruction: '指令遵循' };

const lines = ['# 大模型智能水平测试报告', ''];

if (selection) {
  const diff = Object.entries(selection.distribution?.difficulty ?? {})
    .map(([k, v]) => `${difficultyName[k] ?? k} ${v}`)
    .join('；');
  const ability = Object.entries(selection.distribution?.ability ?? {})
    .map(([k, v]) => `${abilityName[k] ?? k} ${v}`)
    .join('；');

  lines.push(
    '## 本轮抽题',
    '',
    `- 中国日期：${selection.runDate}`,
    `- 题库规模：${selection.bankCanonicalQuestions} 道原始题`,
    `- 本轮：${selection.anchorCount} 道固定锚点 + ${selection.rotatingCount} 道轮换题 = ${selection.canonicalQuestionsSelected} 道原始题 / ${selection.bilingualTestsSelected} 个中英文测试`,
    `- 固定锚点：${selection.anchors.join(', ')}`,
    `- 轮换题：${selection.rotating.join(', ')}`,
    `- 难度分布：${diff}`,
    `- 能力分布：${ability}`,
    '',
  );
}

lines.push(
  '## 总览',
  '',
  '| 模型 | 有效回答正确率 | 正确/答错 | 超时 | API错误 | 中文 | 英文 | 总令牌（Token） | 有效回答平均时间 |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---:|',
);

for (const p of providers) {
  const o = p.overall;
  lines.push(
    `| ${p.provider} | ${o.passed}/${o.answered}（${pct(o.answeredPassRate)}） | ${o.passed}/${o.wrong} | ${o.timeouts} | ${o.apiErrors} | ${p.languages.zh.passed}/${p.languages.zh.answered}（${pct(p.languages.zh.answeredPassRate)}） | ${p.languages.en.passed}/${p.languages.en.answered}（${pct(p.languages.en.answeredPassRate)}） | ${fmt(o.tokenUsage.total)} | ${latency(o.averageLatencyMs)} |`,
  );
}

lines.push(
  '',
  '> 注：超时/API错误不再计入“普通答错”；有效回答正确率只在实际返回答案的测试中计算。超时仍单独保留为重要异常指标。',
  '',
  '## 固定锚点：推理投入监控',
  '',
  '固定锚点只比较每天重复出现的同一批题。响应时间和平均 Token 均排除超时/API错误，避免异常请求污染正常基线。',
  '',
  '| 模型 | 有效回答正确率 | 答错 | 超时 | API错误 | 平均响应时间 | 平均输出 Token | 平均 Reasoning Token* | 平均总 Token |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---:|',
);

for (const p of providers) {
  const a = p.anchor;
  lines.push(
    `| ${p.provider} | ${a.passed}/${a.answered}（${pct(a.answeredPassRate)}） | ${a.wrong} | ${a.timeouts} | ${a.apiErrors} | ${latency(a.averageLatencyMs)} | ${fmt(a.averageTokens.completion, 1)} | ${fmt(a.averageTokens.reasoning, 1)} | ${fmt(a.averageTokens.total, 1)} |`,
  );
}

lines.push(
  '',
  '\* Reasoning Token 只有上游接口明确返回时才单独统计，且通常已包含在输出/总 Token 中。',
  '',
  '### 中英文分歧题',
  '',
);

for (const p of providers) {
  const items = p.pairComparison.disagreementPairs;
  lines.push(
    `- ${p.provider}：${items.length ? items.map((x) => `${x.pairId}（${x.better === 'zh' ? '中文更好' : '英文更好'}）`).join('、') : '无'}`,
  );
}

for (const p of providers) {
  lines.push('', `## ${p.provider}`, '');
  lines.push(
    `- 有效回答正确率：${p.overall.passed}/${p.overall.answered}（${pct(p.overall.answeredPassRate)}）`,
    `- 普通答错：${p.overall.wrong}；超时：${p.overall.timeouts}；API错误：${p.overall.apiErrors}`,
    `- 中文：${p.languages.zh.passed}/${p.languages.zh.answered}（${pct(p.languages.zh.answeredPassRate)}）`,
    `- 英文：${p.languages.en.passed}/${p.languages.en.answered}（${pct(p.languages.en.answeredPassRate)}）`,
    `- 固定锚点有效回答：${p.anchor.passed}/${p.anchor.answered}（${pct(p.anchor.answeredPassRate)}）`,
    `- 同题中英文比较：中文更好 ${p.pairComparison.zhBetter} 题；英文更好 ${p.pairComparison.enBetter} 题；相同 ${p.pairComparison.equal} 题。`,
    '',
    '| 能力类别 | 有效正确率 | 答错 | 超时 | API错误 |',
    '|---|---:|---:|---:|---:|',
  );

  for (const [name, c] of Object.entries(p.categories)) {
    lines.push(
      `| ${categoryName[name] ?? name} | ${c.all.passed}/${c.all.answered}（${pct(c.all.answeredPassRate)}） | ${c.all.wrong} | ${c.all.timeouts} | ${c.all.apiErrors} |`,
    );
  }
}

fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
