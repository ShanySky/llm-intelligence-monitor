import fs from 'node:fs';

const input = process.argv[2] ?? 'results/results.json';
const outJson = process.argv[3] ?? 'results/summary.json';
const outMd = process.argv[4] ?? 'results/summary.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const selectionPath = 'results/selection.json';
const selection = fs.existsSync(selectionPath) ? JSON.parse(fs.readFileSync(selectionPath, 'utf8')) : null;
const rows = data?.results?.results ?? data?.results?.outputs ?? data?.results ?? [];

const num = (v) => Number.isFinite(v) ? v : 0;
const freshStats = () => ({
  total: 0, passed: 0, errors: 0, scoreSum: 0,
  latencySum: 0, latencyCount: 0, costUsd: 0,
  tokenUsage: { prompt: 0, completion: 0, reasoning: 0, cached: 0, total: 0, numRequests: 0 },
});
const addRow = (s, row) => {
  s.total += 1;
  s.passed += row?.success ? 1 : 0;
  s.errors += row?.error ? 1 : 0;
  s.scoreSum += num(row?.score);
  if (Number.isFinite(row?.latencyMs)) {
    s.latencySum += row.latencyMs;
    s.latencyCount += 1;
  }
  s.costUsd += num(row?.cost ?? row?.response?.cost);
  const u = row?.tokenUsage ?? row?.response?.tokenUsage ?? {};
  s.tokenUsage.prompt += num(u.prompt);
  s.tokenUsage.completion += num(u.completion);
  s.tokenUsage.cached += num(u.cached);
  s.tokenUsage.total += num(u.total);
  s.tokenUsage.numRequests += num(u.numRequests) || 1;
  s.tokenUsage.reasoning += num(u?.completionDetails?.reasoning);
};
const finish = (s) => ({
  total: s.total,
  passed: s.passed,
  failed: s.total - s.passed,
  errors: s.errors,
  passRate: s.total ? s.passed / s.total : 0,
  averageScore: s.total ? s.scoreSum / s.total : 0,
  averageLatencyMs: s.latencyCount ? s.latencySum / s.latencyCount : null,
  estimatedCostUsd: s.costUsd,
  tokenUsage: s.tokenUsage,
});

const buckets = new Map();
const bucketFor = (name) => {
  if (!buckets.has(name)) {
    buckets.set(name, {
      provider: name,
      overall: freshStats(),
      languages: { zh: freshStats(), en: freshStats() },
      categories: {},
      pairs: {},
    });
  }
  return buckets.get(name);
};

for (const row of rows) {
  const provider = row?.provider?.label ?? row?.provider?.id ?? row?.provider ?? '未知模型';
  const vars = row?.vars ?? row?.testCase?.vars ?? {};
  const category = vars.category ?? 'uncategorized';
  const language = vars.language ?? 'unknown';
  const pairId = vars.pair_id ?? 'unknown';

  const b = bucketFor(provider);
  addRow(b.overall, row);
  if (b.languages[language]) addRow(b.languages[language], row);

  if (!b.categories[category]) b.categories[category] = { all: freshStats(), zh: freshStats(), en: freshStats() };
  addRow(b.categories[category].all, row);
  if (b.categories[category][language]) addRow(b.categories[category][language], row);

  if (!b.pairs[pairId]) b.pairs[pairId] = { zh: freshStats(), en: freshStats() };
  if (b.pairs[pairId][language]) addRow(b.pairs[pairId][language], row);
}

const providers = [...buckets.values()].map((b) => {
  const pairComparison = { zhBetter: 0, enBetter: 0, equal: 0, comparablePairs: 0 };
  for (const p of Object.values(b.pairs)) {
    if (!p.zh.total || !p.en.total) continue;
    pairComparison.comparablePairs += 1;
    const zr = p.zh.passed / p.zh.total;
    const er = p.en.passed / p.en.total;
    if (zr > er) pairComparison.zhBetter += 1;
    else if (er > zr) pairComparison.enBetter += 1;
    else pairComparison.equal += 1;
  }

  return {
    provider: b.provider,
    overall: finish(b.overall),
    languages: { zh: finish(b.languages.zh), en: finish(b.languages.en) },
    languageGapPctPoints:
      (b.languages.zh.total ? b.languages.zh.passed / b.languages.zh.total : 0) * 100 -
      (b.languages.en.total ? b.languages.en.passed / b.languages.en.total : 0) * 100,
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

const fmt = (n) => Number(n ?? 0).toLocaleString('en-US');
const pct = (r) => `${(Number(r ?? 0) * 100).toFixed(1)}%`;
const latency = (v) => v == null ? '无' : `${Math.round(v)} 毫秒`;
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

const lines = [
  '# 大模型智能水平测试报告',
  '',
];

if (selection) {
  const diff = Object.entries(selection.distribution?.difficulty ?? {}).map(([k,v]) => `${difficultyName[k] ?? k} ${v}`).join('；');
  const ability = Object.entries(selection.distribution?.ability ?? {}).map(([k,v]) => `${abilityName[k] ?? k} ${v}`).join('；');
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
  '| 模型 | 总成绩 | 中文成绩 | 英文成绩 | 中文-英文差值 | 输入令牌（Token） | 输出令牌（Token） | 推理令牌（Token）* | 总令牌（Token） | 平均延迟 |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
);

for (const p of providers) {
  const o = p.overall;
  lines.push(
    `| ${p.provider} | ${o.passed}/${o.total}（${pct(o.passRate)}） | ${p.languages.zh.passed}/${p.languages.zh.total}（${pct(p.languages.zh.passRate)}） | ${p.languages.en.passed}/${p.languages.en.total}（${pct(p.languages.en.passRate)}） | ${p.languageGapPctPoints >= 0 ? '+' : ''}${p.languageGapPctPoints.toFixed(1)} 个百分点 | ${fmt(o.tokenUsage.prompt)} | ${fmt(o.tokenUsage.completion)} | ${fmt(o.tokenUsage.reasoning)} | ${fmt(o.tokenUsage.total)} | ${latency(o.averageLatencyMs)} |`,
  );
}

lines.push(
  '',
  '\* 推理令牌只有在上游接口或中转明确返回时才会单独统计；它通常已经包含在输出令牌/总令牌中，不应再次相加。',
);

for (const p of providers) {
  lines.push('', `## ${p.provider}`, '');
  lines.push(
    `- 总成绩：${p.overall.passed}/${p.overall.total}（${pct(p.overall.passRate)}）`,
    `- 中文：${p.languages.zh.passed}/${p.languages.zh.total}（${pct(p.languages.zh.passRate)}），总令牌 ${fmt(p.languages.zh.tokenUsage.total)}`,
    `- 英文：${p.languages.en.passed}/${p.languages.en.total}（${pct(p.languages.en.passRate)}），总令牌 ${fmt(p.languages.en.tokenUsage.total)}`,
    `- 同题中英文比较：中文更好 ${p.pairComparison.zhBetter} 题；英文更好 ${p.pairComparison.enBetter} 题；相同 ${p.pairComparison.equal} 题。`,
    '',
    '| 能力类别 | 汇总 | 中文 | 英文 |',
    '|---|---:|---:|---:|',
  );
  for (const [name, c] of Object.entries(p.categories)) {
    lines.push(
      `| ${categoryName[name] ?? name} | ${c.all.passed}/${c.all.total}（${pct(c.all.passRate)}） | ${c.zh.passed}/${c.zh.total}（${pct(c.zh.passRate)}） | ${c.en.passed}/${c.en.total}（${pct(c.en.passRate)}） |`,
    );
  }
}

fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
