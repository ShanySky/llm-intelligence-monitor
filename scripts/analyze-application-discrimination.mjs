import fs from 'node:fs';

const input = process.argv[2] ?? 'results/application-final-summary.json';
const policyPath = process.argv[3] ?? 'benchmarks/application-selection-policy.json';
const outJson = process.argv[4] ?? 'results/application-discrimination.json';
const outMd = process.argv[5] ?? 'results/application-discrimination.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const rows = Array.isArray(data.rows) ? data.rows : [];
const families = data.manifest?.families ?? [];
if (!rows.length) throw new Error('No result rows found');

const q = policy.quality ?? {};
const runtime = policy.runtime ?? {};
const effortRank = { low: 0, medium: 1, high: 2, xhigh: 3 };

const mean = (xs) => xs.length ? xs.reduce((a,b)=>a+b,0)/xs.length : null;
const stdev = (xs) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((s,x)=>s+(x-m)**2,0)/xs.length);
};
const range = (xs) => xs.length ? Math.max(...xs)-Math.min(...xs) : null;

const group = new Map();
for (const r of rows) {
  const key = r.task;
  if (!group.has(key)) group.set(key, []);
  group.get(key).push(r);
}

const tasks = [];
for (const family of families) {
  const rs = group.get(family.id) ?? [];
  const valid = rs.filter((r) => r.data_complete !== false && !r.infrastructure_error);

  const byConfig = new Map();
  for (const r of valid) {
    const key = `${r.model}|${r.effort}`;
    if (!byConfig.has(key)) byConfig.set(key, []);
    byConfig.get(key).push(r);
  }

  const configStats = [...byConfig.entries()].map(([key, xs]) => ({
    key,
    model: xs[0].model,
    effort: xs[0].effort,
    trials: xs.length,
    average_score: mean(xs.map(x=>Number(x.score ?? 0))),
    stddev_score: stdev(xs.map(x=>Number(x.score ?? 0))),
    average_duration_seconds: mean(xs.map(x=>Number(x.duration_seconds ?? 0))),
    average_input_tokens: mean(xs.map(x=>Number(x.usage?.input_tokens ?? 0))),
    average_reasoning_tokens: mean(xs.map(x=>Number(x.usage?.reasoning_tokens ?? 0))),
  }));

  const xhighModels = configStats.filter((x) => x.effort === 'xhigh');
  const xhighScores = xhighModels.map((x) => x.average_score).filter(Number.isFinite);
  const solEfforts = configStats
    .filter((x) => x.model === 'gpt-6-sol')
    .sort((a,b)=>(effortRank[a.effort]??99)-(effortRank[b.effort]??99));
  const solScores = solEfforts.map((x) => x.average_score).filter(Number.isFinite);

  const modelSpread = range(xhighScores);
  const effortSpread = range(solScores);
  const maxStd = configStats.length ? Math.max(...configStats.map((x)=>x.stddev_score ?? 0)) : null;
  const ceilingConfigs = configStats.filter((x) => x.average_score >= Number(q.ceiling_score ?? 95)).length;
  const ceilingRate = configStats.length ? ceilingConfigs/configStats.length : null;
  const maxDuration = configStats.length ? Math.max(...configStats.map((x)=>x.average_duration_seconds ?? 0)) : null;

  const stable = maxStd == null || maxStd <= Number(q.max_repeat_stddev_points ?? 12);
  const withinBudget = maxDuration == null || maxDuration <= Number(runtime.hard_limit_seconds ?? 600);
  const modelDiscriminator = modelSpread != null && modelSpread >= Number(q.min_model_spread_points ?? 10);
  const effortDiscriminator = effortSpread != null && effortSpread >= Number(q.min_effort_spread_points ?? 10);

  let classification;
  if (!withinBudget) classification = 'too-slow';
  else if (!stable) classification = 'noisy';
  else if (modelDiscriminator && effortDiscriminator) classification = 'model+effort-discriminator';
  else if (modelDiscriminator) classification = 'model-discriminator';
  else if (effortDiscriminator) classification = 'effort-discriminator';
  else if (ceilingRate != null && ceilingRate >= 0.8) classification = 'coverage-only-ceiling';
  else classification = 'coverage-or-needs-more-data';

  tasks.push({
    task: family.id,
    family: family.family,
    weight: family.weight,
    classification,
    model_spread_points: modelSpread,
    sol_effort_spread_points: effortSpread,
    max_repeat_stddev_points: maxStd,
    ceiling_rate: ceilingRate,
    max_average_duration_seconds: maxDuration,
    stable,
    within_budget: withinBudget,
    config_stats: configStats,
  });
}

const output = {
  generated_at: new Date().toISOString(),
  policy,
  tasks,
  counts: Object.fromEntries(
    [...new Set(tasks.map(x=>x.classification))].map(k=>[k,tasks.filter(x=>x.classification===k).length])
  ),
};
fs.writeFileSync(outJson, JSON.stringify(output,null,2)+'\n');

const f1 = (v) => v == null ? '-' : Number(v).toFixed(1);
const pct = (v) => v == null ? '-' : (v*100).toFixed(0)+'%';
const lines = [
  '# Application Task Discrimination Analysis',
  '',
  '| Task | Family | Class | XHigh model spread | Sol effort spread | Repeat stddev | Ceiling rate | Max avg runtime |',
  '|---|---|---|---:|---:|---:|---:|---:|',
];
for (const x of tasks) {
  lines.push(`| ${x.task} | ${x.family} | ${x.classification} | ${f1(x.model_spread_points)} | ${f1(x.sol_effort_spread_points)} | ${f1(x.max_repeat_stddev_points)} | ${pct(x.ceiling_rate)} | ${x.max_average_duration_seconds == null ? '-' : Math.round(x.max_average_duration_seconds)+'s'} |`);
}
lines.push(
  '',
  '> Selection rule: prefer stable, in-budget tasks with real between-model or between-effort score spread. Application-critical tasks may remain as coverage checks even when saturated. Effort monotonicity is not assumed or forced.',
  ''
);
fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
