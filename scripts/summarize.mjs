import fs from 'node:fs';

const input = process.argv[2] ?? 'results/results.json';
const outJson = process.argv[3] ?? 'results/summary.json';
const outMd = process.argv[4] ?? 'results/summary.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const rows = data?.results?.results ?? data?.results?.outputs ?? data?.results ?? [];

const buckets = new Map();

function bucketFor(name) {
  if (!buckets.has(name)) {
    buckets.set(name, {
      provider: name,
      total: 0,
      passed: 0,
      errors: 0,
      scoreSum: 0,
      latencySum: 0,
      latencyCount: 0,
      costUsd: 0,
      tokenUsage: {
        prompt: 0,
        completion: 0,
        reasoning: 0,
        cached: 0,
        total: 0,
        numRequests: 0,
      },
      categories: {},
    });
  }
  return buckets.get(name);
}

function number(value) {
  return Number.isFinite(value) ? value : 0;
}

for (const row of rows) {
  const provider =
    row?.provider?.label ??
    row?.provider?.id ??
    row?.provider ??
    'unknown-provider';

  const category =
    row?.vars?.category ??
    row?.testCase?.vars?.category ??
    'uncategorized';

  const b = bucketFor(provider);
  b.total += 1;
  b.passed += row?.success ? 1 : 0;
  b.errors += row?.error ? 1 : 0;
  b.scoreSum += number(row?.score);

  if (Number.isFinite(row?.latencyMs)) {
    b.latencySum += row.latencyMs;
    b.latencyCount += 1;
  }

  b.costUsd += number(row?.cost ?? row?.response?.cost);

  const usage = row?.tokenUsage ?? row?.response?.tokenUsage ?? {};
  b.tokenUsage.prompt += number(usage.prompt);
  b.tokenUsage.completion += number(usage.completion);
  b.tokenUsage.cached += number(usage.cached);
  b.tokenUsage.total += number(usage.total);
  b.tokenUsage.numRequests += number(usage.numRequests) || 1;
  b.tokenUsage.reasoning += number(usage?.completionDetails?.reasoning);

  if (!b.categories[category]) {
    b.categories[category] = { total: 0, passed: 0, scoreSum: 0 };
  }
  const c = b.categories[category];
  c.total += 1;
  c.passed += row?.success ? 1 : 0;
  c.scoreSum += number(row?.score);
}

const providers = [...buckets.values()].map((b) => ({
  provider: b.provider,
  total: b.total,
  passed: b.passed,
  failed: b.total - b.passed,
  errors: b.errors,
  passRate: b.total ? b.passed / b.total : 0,
  averageScore: b.total ? b.scoreSum / b.total : 0,
  averageLatencyMs: b.latencyCount ? b.latencySum / b.latencyCount : null,
  estimatedCostUsd: b.costUsd,
  tokenUsage: b.tokenUsage,
  categories: Object.fromEntries(
    Object.entries(b.categories).map(([name, c]) => [
      name,
      {
        total: c.total,
        passed: c.passed,
        passRate: c.total ? c.passed / c.total : 0,
        averageScore: c.total ? c.scoreSum / c.total : 0,
      },
    ]),
  ),
}));

const summary = {
  generatedAt: new Date().toISOString(),
  evalTimestamp: data?.timestamp ?? data?.results?.timestamp ?? null,
  evalId: data?.evalId ?? data?.results?.evalId ?? null,
  providers,
};

fs.mkdirSync(new URL('../results/', import.meta.url), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(summary, null, 2) + '\n');

const fmt = (n) => Number(n ?? 0).toLocaleString('en-US');
const money = (n) => Number(n ?? 0) > 0 ? `$${Number(n).toFixed(6)}` : 'n/a';

const lines = [
  '# LLM intelligence test summary',
  '',
  '## Model totals',
  '',
  '| Provider | Pass | Pass rate | Input tokens | Output tokens | Reasoning tokens* | Cached tokens | Total tokens | Est. cost | Avg latency |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|',
];

for (const p of providers) {
  const latency = p.averageLatencyMs == null ? 'n/a' : `${Math.round(p.averageLatencyMs)} ms`;
  lines.push(
    `| ${p.provider} | ${p.passed}/${p.total} | ${(p.passRate * 100).toFixed(1)}% | ${fmt(p.tokenUsage.prompt)} | ${fmt(p.tokenUsage.completion)} | ${fmt(p.tokenUsage.reasoning)} | ${fmt(p.tokenUsage.cached)} | ${fmt(p.tokenUsage.total)} | ${money(p.estimatedCostUsd)} | ${latency} |`,
  );
}

lines.push(
  '',
  '\* Reasoning tokens are shown only when the upstream API/gateway reports them. They are generally already included in output/total usage rather than added again.',
);

for (const p of providers) {
  lines.push('', `## ${p.provider}`, '');
  lines.push('| Category | Pass | Pass rate | Avg score |');
  lines.push('|---|---:|---:|---:|');
  for (const [category, c] of Object.entries(p.categories)) {
    lines.push(
      `| ${category} | ${c.passed}/${c.total} | ${(c.passRate * 100).toFixed(1)}% | ${c.averageScore.toFixed(3)} |`,
    );
  }
}

fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
