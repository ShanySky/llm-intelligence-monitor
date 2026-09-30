import fs from 'node:fs';
import path from 'node:path';

const historyDir = process.argv[2] ?? 'history-store/history';
const currentPath = process.argv[3] ?? 'results/summary.json';
const metadataPath = process.argv[4] ?? 'tests/question-metadata.json';
const outJson = process.argv[5] ?? 'results/question-health.json';
const outMd = process.argv[6] ?? 'results/question-health.md';
const configPath = process.argv[7] ?? 'monitor-config.json';

const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const anchorPool = new Set(config?.daily?.anchorPool ?? []);
const activeAnchorCount = Number(config?.daily?.anchorCount ?? 0);
const activeAnchors = new Set((config?.daily?.anchorPool ?? []).slice(0, activeAnchorCount));
const current = JSON.parse(fs.readFileSync(currentPath, 'utf8'));
const minDays = 3;

const docs = [];
if (fs.existsSync(historyDir)) {
  for (const name of fs.readdirSync(historyDir).filter((x) => x.endsWith('.json')).sort()) {
    try {
      const value = JSON.parse(fs.readFileSync(path.join(historyDir, name), 'utf8'));
      docs.push(value);
    } catch {
      // A malformed historical file must not break the daily monitor.
    }
  }
}
const currentDay = current?.selection?.runDate ?? String(current?.generatedAt ?? '').slice(0, 10);
const uniqueDocs = docs.filter((doc) => {
  const day = doc?.selection?.runDate ?? String(doc?.generatedAt ?? '').slice(0, 10);
  return !currentDay || day !== currentDay;
});
uniqueDocs.push(current);

const observations = new Map();
const daySpreads = new Map();

for (const doc of uniqueDocs) {
  const day = doc?.selection?.runDate ?? String(doc?.generatedAt ?? '').slice(0, 10);
  if (!day) continue;
  for (const provider of doc?.providers ?? []) {
    const stats = provider?.questionStats;
    if (!stats || typeof stats !== 'object') continue;
    for (const [pairId, q] of Object.entries(stats)) {
      const all = q?.all;
      if (!all || !all.total || all.apiErrors) continue;
      if (!observations.has(pairId)) observations.set(pairId, []);
      observations.get(pairId).push({
        day,
        provider: provider.provider,
        passRate: Number(all.passRate ?? 0),
        zhPassRate: Number(q?.zh?.passRate ?? 0),
        enPassRate: Number(q?.en?.passRate ?? 0),
      });
      const spreadKey = pairId + '|' + day;
      if (!daySpreads.has(spreadKey)) daySpreads.set(spreadKey, []);
      daySpreads.get(spreadKey).push(Number(all.passRate ?? 0));
    }
  }
}

const mean = (xs) => xs.length ? xs.reduce((a,b)=>a+b,0)/xs.length : null;
const stdev = (xs) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((s,x)=>s+(x-m)**2,0)/xs.length);
};

const questions = {};
for (const pairId of Object.keys(metadata)) {
  const xs = observations.get(pairId) ?? [];
  const days = [...new Set(xs.map((x) => x.day))];
  const rates = xs.map((x) => x.passRate);
  const ceilingRate = xs.length ? xs.filter((x) => x.passRate >= 1).length / xs.length : null;
  const languageDisagreementRate = xs.length
    ? xs.filter((x) => x.zhPassRate !== x.enPassRate).length / xs.length
    : null;

  const spreads = days.map((day) => {
    const vals = daySpreads.get(pairId + '|' + day) ?? [];
    return vals.length ? Math.max(...vals) - Math.min(...vals) : 0;
  });
  const maxModelSpread = spreads.length ? Math.max(...spreads) : null;
  const avgModelSpread = mean(spreads);

  let classification = 'insufficient-data';
  let selectionWeight = 1;
  if (days.length >= minDays) {
    const avg = mean(rates) ?? 0;
    const variability = stdev(rates);
    if (ceilingRate >= 0.9 && (maxModelSpread ?? 0) <= 0.25) {
      classification = 'stable-ceiling';
      selectionWeight = 0.2;
    } else if ((maxModelSpread ?? 0) >= 0.5 || (avgModelSpread ?? 0) >= 0.25) {
      classification = 'model-discriminator';
      selectionWeight = 2;
    } else if (avg >= 0.2 && avg <= 0.9) {
      classification = 'useful-difficulty';
      selectionWeight = 1.5;
    } else if (variability >= 0.3 && (avgModelSpread ?? 0) < 0.25) {
      classification = 'noisy';
      selectionWeight = 0.5;
    } else {
      classification = 'coverage';
      selectionWeight = 1;
    }
  }

  questions[pairId] = {
    pairId,
    ...metadata[pairId],
    sampledDays: days.length,
    observations: xs.length,
    averagePassRate: mean(rates),
    passRateStddev: stdev(rates),
    ceilingObservationRate: ceilingRate,
    maxDailyModelSpread: maxModelSpread,
    averageDailyModelSpread: avgModelSpread,
    languageDisagreementRate,
    classification,
    selectionWeight,
    inAnchorPool: anchorPool.has(pairId),
    activeAnchor: activeAnchors.has(pairId),
    anchorRecommendation:
      activeAnchors.has(pairId) && classification === 'stable-ceiling'
        ? 'retire-at-next-anchor-epoch'
        : 'keep',
  };
}

const recommendedAnchorRetirements = Object.values(questions)
  .filter((q) => q.anchorRecommendation === 'retire-at-next-anchor-epoch')
  .map((q) => q.pairId);

const output = {
  generatedAt: new Date().toISOString(),
  minDaysForClassification: minDays,
  sourceDays: [...new Set([...observations.values()].flat().map((x) => x.day))].sort(),
  activeAnchors: [...activeAnchors],
  recommendedAnchorRetirements,
  questions,
};
fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const pct = (v) => v == null ? '-' : (v * 100).toFixed(0) + '%';
const f1 = (v) => v == null ? '-' : Number(v).toFixed(2);
const rows = Object.values(questions).sort((a,b) =>
  b.sampledDays - a.sampledDays ||
  b.selectionWeight - a.selectionWeight ||
  a.pairId.localeCompare(b.pairId)
);
const lines = [
  '# 快速题目健康度',
  '',
  '| 题目 | 能力 | 样本天数 | 平均正确率 | 最大模型差 | 中英分歧 | 分类 | 轮换权重 | Anchor |',
  '|---|---|---:|---:|---:|---:|---|---:|---|',
];
for (const q of rows) {
  const anchor = q.activeAnchor
    ? (q.anchorRecommendation === 'retire-at-next-anchor-epoch' ? '退役候选' : '固定')
    : '-';
  lines.push(`| ${q.pairId} | ${q.ability} | ${q.sampledDays} | ${pct(q.averagePassRate)} | ${pct(q.maxDailyModelSpread)} | ${pct(q.languageDisagreementRate)} | ${q.classification} | ${f1(q.selectionWeight)} | ${anchor} |`);
}
lines.push(
  '',
  '## 固定锚点退役建议',
  '',
  recommendedAnchorRetirements.length
    ? `建议在下一次 anchor 版本切换时替换：${recommendedAnchorRetirements.join(', ')}`
    : '当前没有达到退役条件的固定锚点。',
  '',
  '> 只有至少 3 个正式日测样本日后才自动分类。stable-ceiling 会立即在轮换抽题中降权；固定锚点不会日常自动变更，而是在明确的 anchor 版本切换时按退役建议替换，以保留历史可比性。',
  ''
);
fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
