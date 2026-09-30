import fs from 'node:fs';
import path from 'node:path';

const inputDir = process.argv[2] ?? 'results/frontier-stability';
const targetPath = process.argv[3] ?? 'benchmarks/frontier-stability-target.json';
const outJson = process.argv[4] ?? 'results/frontier-stability-summary.json';
const outMd = process.argv[5] ?? 'results/frontier-stability-summary.md';

const target = JSON.parse(fs.readFileSync(targetPath, 'utf8'));
const rows = [];

function walk(p) {
  if (!fs.existsSync(p)) return;
  for (const ent of fs.readdirSync(p, { withFileTypes: true })) {
    const full = path.join(p, ent.name);
    if (ent.isDirectory()) walk(full);
    else if (ent.name === 'result.json') {
      try {
        rows.push(JSON.parse(fs.readFileSync(full, 'utf8')));
      } catch {}
    }
  }
}
walk(inputDir);
if (!rows.length) throw new Error('No frontier stability rows found');

const effortRank = { low: 0, medium: 1, high: 2, xhigh: 3 };
const mean = (xs) => xs.length ? xs.reduce((a,b)=>a+b,0)/xs.length : null;
const stdev = (xs) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((s,x)=>s+(x-m)**2,0)/xs.length);
};

const groups = new Map();
for (const r of rows) {
  if (r.data_complete === false || r.infrastructure_error) continue;
  const key = r.effort;
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(r);
}

const efforts = [...groups.entries()]
  .map(([effort, xs]) => {
    const scores = xs.map(x=>Number(x.score ?? 0));
    const checks = {};
    for (const r of xs) {
      for (const [name, c] of Object.entries(r.checks ?? {})) {
        if (!checks[name]) checks[name] = { passed: 0, total: 0, points: Number(c?.points ?? 0) };
        checks[name].total += 1;
        if (c?.passed) checks[name].passed += 1;
      }
    }
    const checkPassRates = Object.fromEntries(
      Object.entries(checks).map(([name, c]) => [name, {
        points: c.points,
        pass_rate: c.total ? c.passed / c.total : null,
        passed: c.passed,
        trials: c.total,
      }])
    );
    return {
      effort,
      trials: xs.length,
      scores,
      mean_score: mean(scores),
      min_score: Math.min(...scores),
      max_score: Math.max(...scores),
      stddev_score: stdev(scores),
      average_duration_seconds: mean(xs.map(x=>Number(x.duration_seconds ?? 0))),
      average_shell_commands: mean(xs.map(x=>Number(x.shell_commands ?? 0))),
      average_input_tokens: mean(xs.map(x=>Number(x.usage?.input_tokens ?? 0))),
      average_output_tokens: mean(xs.map(x=>Number(x.usage?.output_tokens ?? 0))),
      average_reasoning_tokens: mean(xs.map(x=>Number(x.usage?.reasoning_tokens ?? 0))),
      any_budget_saturation: xs.some(x=>x.turn_limit_reached || x.shell_budget_reached),
      check_pass_rates: checkPassRates,
    };
  })
  .sort((a,b)=>(effortRank[a.effort]??99)-(effortRank[b.effort]??99));

const byEffort = Object.fromEntries(efforts.map(x=>[x.effort,x]));
const medium = byEffort.medium ?? null;
const high = byEffort.high ?? null;
const xhigh = byEffort.xhigh ?? null;
const maxStddev = efforts.length ? Math.max(...efforts.map(x=>x.stddev_score)) : null;
const stable = maxStddev != null && maxStddev <= 12;
const enoughTrials = efforts.length &&
  efforts.every(x=>x.trials >= Number(target.trials ?? 2));
const budgetConfounded = efforts.some(x=>x.any_budget_saturation);
const directionalGain = medium && xhigh ? xhigh.mean_score - medium.mean_score : null;
const monotonic = medium && high && xhigh
  ? medium.mean_score <= high.mean_score && high.mean_score <= xhigh.mean_score
  : null;

let classification = 'needs-more-data';
if (budgetConfounded) classification = 'budget-confounded';
else if (!enoughTrials) classification = 'needs-more-data';
else if (!stable) classification = 'noisy';
else if (directionalGain != null && directionalGain >= 10 && monotonic !== false) {
  classification = 'confirmed-effort-discriminator';
} else {
  classification = 'no-confirmed-effort-signal';
}

const output = {
  generated_at: new Date().toISOString(),
  target,
  task: target.task,
  model: target.model,
  efforts,
  max_stddev_score: maxStddev,
  stable,
  enough_trials: enoughTrials,
  budget_confounded: budgetConfounded,
  medium_to_xhigh_gain_points: directionalGain,
  monotonic_medium_high_xhigh: monotonic,
  classification,
};

fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const f1 = (v) => v == null ? '-' : Number(v).toFixed(1);
const lines = [
  '# Frontier Stability Validation',
  '',
  `Task: ${target.task} · Model: ${target.model}`,
  '',
  '| Effort | Trials | Scores | Mean | Stddev | Runtime | Shell | Input tokens | Reasoning tokens | Budget saturated |',
  '|---|---:|---|---:|---:|---:|---:|---:|---:|:---:|',
];
for (const x of efforts) {
  lines.push(
    `| ${x.effort} | ${x.trials} | ${x.scores.join(', ')} | ${f1(x.mean_score)} | ${f1(x.stddev_score)} | ` +
    `${Math.round(x.average_duration_seconds)}s | ${f1(x.average_shell_commands)} | ${Math.round(x.average_input_tokens)} | ` +
    `${Math.round(x.average_reasoning_tokens)} | ${x.any_budget_saturation ? 'yes' : 'no'} |`
  );
}
lines.push(
  '',
  `**Classification:** \`${classification}\``,
  '',
  `Medium→X High mean gain: ${f1(directionalGain)} points; max repeat stddev: ${f1(maxStddev)}; monotonic M≤H≤XH: ${monotonic == null ? '-' : (monotonic ? 'yes' : 'no')}.`,
  '',
  '## Failure-domain pass rates',
  ''
);

const allChecks = new Set();
for (const x of efforts) for (const k of Object.keys(x.check_pass_rates)) allChecks.add(k);
lines.push('| Check | ' + efforts.map(x=>x.effort).join(' | ') + ' |');
lines.push('|---|' + efforts.map(()=> '---:').join('|') + '|');
for (const check of [...allChecks].sort()) {
  lines.push('| ' + check + ' | ' + efforts.map(x=>{
    const c=x.check_pass_rates[check];
    return c ? (c.pass_rate*100).toFixed(0)+'%' : '-';
  }).join(' | ') + ' |');
}
lines.push(
  '',
  '> A quality gap is confirmed only after repeated trials, nonbinding budgets, acceptable variance, and directionally coherent effort behavior.',
  ''
);
fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
