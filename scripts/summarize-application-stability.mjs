import fs from 'node:fs';
import path from 'node:path';

const repeatDir = process.argv[2] ?? 'results/application-stability';
const baselinePath = process.argv[3] ?? 'results/application-final-baseline.json';
const task = process.argv[4] ?? 'hard-review';
const outJson = process.argv[5] ?? 'results/application-stability-summary.json';
const outMd = process.argv[6] ?? 'results/application-stability-summary.md';

const rows = [];

if (fs.existsSync(baselinePath)) {
  const baseline = JSON.parse(fs.readFileSync(baselinePath, 'utf8'));
  for (const r of baseline.rows ?? []) {
    if (r.task === task && r.data_complete !== false && !r.infrastructure_error) {
      rows.push({ ...r, source: 'baseline' });
    }
  }
}

function walk(p) {
  if (!fs.existsSync(p)) return;
  for (const ent of fs.readdirSync(p, { withFileTypes: true })) {
    const full = path.join(p, ent.name);
    if (ent.isDirectory()) walk(full);
    else if (ent.name === 'result.json') {
      try {
        const r = JSON.parse(fs.readFileSync(full, 'utf8'));
        if (r.task === task && r.data_complete !== false && !r.infrastructure_error) {
          rows.push({ ...r, source: 'repeat' });
        }
      } catch {}
    }
  }
}
walk(repeatDir);

if (!rows.length) throw new Error('No stability rows found');

const key = (r) => `${r.model}|${r.effort}`;
const groups = new Map();
for (const r of rows) {
  const k = key(r);
  if (!groups.has(k)) groups.set(k, []);
  groups.get(k).push(r);
}

const mean = (xs) => xs.reduce((a,b)=>a+b,0)/xs.length;
const stdev = (xs) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((s,x)=>s+(x-m)**2,0)/xs.length);
};
const effortRank = { low:0, medium:1, high:2, xhigh:3 };

const configs = [...groups.entries()].map(([k,xs]) => {
  const scores = xs.map(x=>Number(x.score ?? 0));
  const durations = xs.map(x=>Number(x.duration_seconds ?? 0));
  const inputTokens = xs.map(x=>Number(x.usage?.input_tokens ?? 0));
  const reasoningTokens = xs.map(x=>Number(x.usage?.reasoning_tokens ?? 0));
  return {
    key:k,
    model:xs[0].model,
    effort:xs[0].effort,
    trials:xs.length,
    scores,
    mean_score:mean(scores),
    min_score:Math.min(...scores),
    max_score:Math.max(...scores),
    stddev_score:stdev(scores),
    average_duration_seconds:mean(durations),
    average_input_tokens:mean(inputTokens),
    average_reasoning_tokens:mean(reasoningTokens),
    stable:stdev(scores) <= 12,
  };
}).sort((a,b)=>a.model.localeCompare(b.model) ||
  (effortRank[a.effort]??99)-(effortRank[b.effort]??99));

const sol = configs.filter(x=>x.model==='gpt-6-sol');
const solSpread = sol.length ? Math.max(...sol.map(x=>x.mean_score))-Math.min(...sol.map(x=>x.mean_score)) : null;
const xhigh = configs.filter(x=>x.effort==='xhigh');
const modelSpread = xhigh.length ? Math.max(...xhigh.map(x=>x.mean_score))-Math.min(...xhigh.map(x=>x.mean_score)) : null;

const output = {
  generated_at:new Date().toISOString(),
  task,
  configs,
  sol_effort_spread_points:solSpread,
  xhigh_model_spread_points:modelSpread,
  all_stable:configs.every(x=>x.stable),
};
fs.mkdirSync(path.dirname(outJson),{recursive:true});
fs.writeFileSync(outJson,JSON.stringify(output,null,2)+'\n');

const f=(v)=>v==null?'-':Number(v).toFixed(1);
const lines=[
  '# Application Stability Validation',
  '',
  `Task: ${task}`,
  '',
  '| Model | Effort | Trials | Scores | Mean | Stddev | Avg runtime | Avg input tokens | Avg reasoning tokens | Stable |',
  '|---|---|---:|---|---:|---:|---:|---:|---:|:---:|',
];
for(const x of configs){
  lines.push(`| ${x.model} | ${x.effort} | ${x.trials} | ${x.scores.join(', ')} | ${f(x.mean_score)} | ${f(x.stddev_score)} | ${Math.round(x.average_duration_seconds)}s | ${Math.round(x.average_input_tokens).toLocaleString()} | ${Math.round(x.average_reasoning_tokens).toLocaleString()} | ${x.stable?'是':'否'} |`);
}
lines.push(
  '',
  `- Sol effort spread: ${f(solSpread)} points`,
  `- X High model spread (tested configs): ${f(modelSpread)} points`,
  `- All tested configs stable (stddev <= 12): ${output.all_stable?'yes':'no'}`,
  ''
);
fs.writeFileSync(outMd,lines.join('\n'));
console.log(lines.join('\n'));
