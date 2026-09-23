import fs from 'node:fs';
import path from 'node:path';

const historyDir = process.argv[2] ?? 'history';
const currentPath = process.argv[3] ?? 'results/summary.json';
const outJson = process.argv[4] ?? 'results/trend.json';
const outMd = process.argv[5] ?? 'results/trend.md';
const configPath = process.argv[6] ?? 'monitor-config.json';

const current = JSON.parse(fs.readFileSync(currentPath, 'utf8'));
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
const detection = config.detection ?? {};

const rollingDays = detection.rollingDays ?? 7;
const minHistoryRuns = detection.minHistoryRuns ?? 3;
const scoreDropThreshold = detection.anchorScoreDropPctPoints ?? 10;
const reasoningDropThreshold = detection.reasoningTokenDropPct ?? 15;
const totalDropThreshold = detection.totalTokenDropPct ?? 10;
const latencyDropThreshold = detection.latencyDropPct ?? 15;
const timeoutIncreaseThreshold = detection.timeoutIncreasePctPoints ?? 10;

const files = fs.existsSync(historyDir)
  ? fs.readdirSync(historyDir).filter((x) => x.endsWith('.json')).sort()
  : [];

const prior = files.slice(-Math.max(rollingDays - 1, 0)).map((name) => {
  try {
    return JSON.parse(fs.readFileSync(path.join(historyDir, name), 'utf8'));
  } catch {
    return null;
  }
}).filter(Boolean);

const pctChange = (cur, base) => {
  if (!Number.isFinite(cur) || !Number.isFinite(base) || base === 0) return null;
  return ((cur - base) / base) * 100;
};

const avg = (values) => {
  const xs = values.filter(Number.isFinite);
  return xs.length ? xs.reduce((a,b)=>a+b,0) / xs.length : null;
};

const modelHistory = (providerName) => {
  const rows = [];
  for (const item of prior) {
    const p = item.providers?.find((x) => x.provider === providerName);
    if (p) rows.push(p);
  }
  return rows;
};

const output = {
  generatedAt: new Date().toISOString(),
  rollingDays,
  priorRunsAvailable: prior.length,
  models: [],
};

for (const p of current.providers ?? []) {
  const hist = modelHistory(p.provider);
  const window = [...hist, p].slice(-rollingDays);

  const anchorBaseline = {
    passRate: avg(hist.map((x) => x.anchor?.answeredPassRate ?? x.anchor?.passRate)),
    timeoutRate: avg(hist.map((x) => x.anchor?.timeoutRate)),
    reasoning: avg(hist.map((x) => x.anchor?.averageTokens?.reasoning)),
    total: avg(hist.map((x) => x.anchor?.averageTokens?.total)),
    latency: avg(hist.map((x) => x.anchor?.averageLatencyMs)),
  };

  const deltas = {
    anchorScorePctPoints:
      anchorBaseline.passRate == null
        ? null
        : ((p.anchor.answeredPassRate ?? p.anchor.passRate) - anchorBaseline.passRate) * 100,
    reasoningTokenPct:
      pctChange(p.anchor.averageTokens.reasoning, anchorBaseline.reasoning),
    totalTokenPct:
      pctChange(p.anchor.averageTokens.total, anchorBaseline.total),
    latencyPct:
      pctChange(p.anchor.averageLatencyMs, anchorBaseline.latency),
    timeoutPctPoints:
      anchorBaseline.timeoutRate == null
        ? null
        : ((p.anchor.timeoutRate ?? 0) - anchorBaseline.timeoutRate) * 100,
  };

  const enoughHistory = hist.length >= minHistoryRuns;
  const scoreDrop = deltas.anchorScorePctPoints != null &&
    deltas.anchorScorePctPoints <= -scoreDropThreshold;
  const reasoningDrop = deltas.reasoningTokenPct != null &&
    deltas.reasoningTokenPct <= -reasoningDropThreshold;
  const totalDrop = deltas.totalTokenPct != null &&
    deltas.totalTokenPct <= -totalDropThreshold;
  const latencyDrop = deltas.latencyPct != null &&
    deltas.latencyPct <= -latencyDropThreshold;
  const timeoutSpike = deltas.timeoutPctPoints != null &&
    deltas.timeoutPctPoints >= timeoutIncreaseThreshold;

  const investmentSignals = [reasoningDrop, totalDrop, latencyDrop].filter(Boolean).length;

  let signal = '基线积累中';
  if (enoughHistory) {
    if (scoreDrop && investmentSignals >= 2) signal = '高度疑似降质/路由异常';
    else if (scoreDrop && investmentSignals >= 1) signal = '疑似降质，建议复测';
    else if (timeoutSpike) signal = '超时率显著上升，检查模型/链路';
    else if (!scoreDrop && investmentSignals === 3) signal = '推理投入显著下降，继续观察';
    else signal = '未见明显异常';
  }

  output.models.push({
    provider: p.provider,
    historyRuns: hist.length,
    rolling: {
      zhPassRate: avg(window.map((x) => x.languages?.zh?.passRate)),
      enPassRate: avg(window.map((x) => x.languages?.en?.passRate)),
      anchorPassRate: avg(window.map((x) => x.anchor?.answeredPassRate ?? x.anchor?.passRate)),
      anchorTimeoutRate: avg(window.map((x) => x.anchor?.timeoutRate)),
      anchorReasoningTokens: avg(window.map((x) => x.anchor?.averageTokens?.reasoning)),
      anchorTotalTokens: avg(window.map((x) => x.anchor?.averageTokens?.total)),
      anchorLatencyMs: avg(window.map((x) => x.anchor?.averageLatencyMs)),
    },
    baseline: anchorBaseline,
    current: {
      anchorPassRate: p.anchor.answeredPassRate ?? p.anchor.passRate,
      anchorTimeoutRate: p.anchor.timeoutRate ?? 0,
      anchorReasoningTokens: p.anchor.averageTokens.reasoning,
      anchorTotalTokens: p.anchor.averageTokens.total,
      anchorLatencyMs: p.anchor.averageLatencyMs,
    },
    deltas,
    flags: { scoreDrop, reasoningDrop, totalDrop, latencyDrop, timeoutSpike },
    signal,
  });
}

fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const f1 = (v) => v == null ? '—' : Number(v).toFixed(1);
const pct = (v) => v == null ? '—' : `${(v * 100).toFixed(1)}%`;
const deltaPct = (v) => v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`;
const deltaPp = (v) => v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(1)} 个百分点`;

const lines = [
  '# 历史趋势与降质信号',
  '',
  `历史正式日测：${prior.length} 次；至少积累 ${minHistoryRuns} 次历史日测后才启用自动异常判断。`,
  '',
  '| 模型 | 近7日中文 | 近7日英文 | 锚点正确率变化 | 超时率变化 | 推理 Token 变化 | 总 Token 变化 | 响应时间变化 | 判断 |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---|',
];

for (const m of output.models) {
  lines.push(
    `| ${m.provider} | ${pct(m.rolling.zhPassRate)} | ${pct(m.rolling.enPassRate)} | ${deltaPp(m.deltas.anchorScorePctPoints)} | ${deltaPp(m.deltas.timeoutPctPoints)} | ${deltaPct(m.deltas.reasoningTokenPct)} | ${deltaPct(m.deltas.totalTokenPct)} | ${deltaPct(m.deltas.latencyPct)} | ${m.signal} |`
  );
}

lines.push(
  '',
  '判定原则：能力下降看有效回答正确率；推理令牌减少、总令牌减少、响应时间缩短属于强化证据。超时率单独监控，不再等同于普通答错。',
);

fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
