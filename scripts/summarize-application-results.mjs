import fs from 'node:fs';
import path from 'node:path';

const dir = process.argv[2] ?? 'results/application';
const manifestPath = process.argv[3] ?? 'benchmarks/application-suite.json';
const outJson = process.argv[4] ?? 'results/application-summary.json';
const outMd = process.argv[5] ?? 'results/application-summary.md';

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const weights = Object.fromEntries(manifest.families.map((x) => [x.id, Number(x.weight)]));

const rows = [];
function walk(p) {
  for (const ent of fs.readdirSync(p, { withFileTypes: true })) {
    const full = path.join(p, ent.name);
    if (ent.isDirectory()) walk(full);
    else if (ent.name === 'result.json') {
      try { rows.push(JSON.parse(fs.readFileSync(full, 'utf8'))); } catch {}
    }
  }
}
if (fs.existsSync(dir)) walk(dir);
if (!rows.length) throw new Error('No application benchmark result.json files found');

const efforts = [...new Set(rows.map((r) => r.effort))].sort();
const totalWeight = manifest.families.reduce((s, x) => s + Number(x.weight), 0);

function rowDataComplete(r) {
  if (typeof r.data_complete === 'boolean') return r.data_complete;
  return !r.infrastructure_error;
}

const byEffort = {};
for (const effort of efforts) {
  const rs = rows.filter((r) => r.effort === effort);
  const valid = rs.filter(rowDataComplete);
  const completeTasks = valid.filter((r) => r.outcome === 'completed' || (!r.outcome && Number(r.agent_exit_code) === 0));

  let qualityWeighted = 0;
  let practicalWeighted = 0;
  let validWeight = 0;
  for (const r of valid) {
    const w = weights[r.task] ?? 0;
    const quality = Number(r.score ?? 0);
    const completed = r.outcome === 'completed' || (!r.outcome && Number(r.agent_exit_code) === 0);
    const practical = quality * 0.85 + (completed ? 15 : 0);
    qualityWeighted += quality * w;
    practicalWeighted += practical * w;
    validWeight += w;
  }

  const allDataComplete = validWeight === totalWeight;
  byEffort[effort] = {
    data_complete: allDataComplete,
    valid_weight: validWeight,
    total_weight: totalWeight,
    quality_score: validWeight ? qualityWeighted / validWeight : null,
    practical_score: validWeight ? practicalWeighted / validWeight : null,
    budget_completion_rate: valid.length ? completeTasks.length / valid.length : null,
    duration_seconds: valid.reduce((s, r) => s + Number(r.duration_seconds ?? 0), 0),
    input_tokens: valid.reduce((s, r) => s + Number(r.usage?.input_tokens ?? 0), 0),
    output_tokens: valid.reduce((s, r) => s + Number(r.usage?.output_tokens ?? 0), 0),
    reasoning_tokens: valid.reduce((s, r) => s + Number(r.usage?.reasoning_tokens ?? 0), 0),
    api_retries: rs.reduce((s, r) => s + Number(r.api_retries ?? 0), 0),
    incomplete_tasks: rs.filter((r) => !rowDataComplete(r)).map((r) => r.task),
  };
}

const summary = { generated_at: new Date().toISOString(), manifest, rows, by_effort: byEffort };
fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(summary, null, 2) + '\n');

const fmt = (n) => n == null ? '-' : Number(n).toLocaleString('en-US');
const pct = (n) => n == null ? '-' : (Number(n) * 100).toFixed(0) + '%';
const cellFor = (family, effort) => {
  const r = rows.find((x) => x.task === family.id && x.effort === effort);
  if (!r) return '-';
  if (!rowDataComplete(r)) return '数据不完整';
  const outcome = r.outcome === 'model_timeout' ? '超时' : '完成';
  return `${Number(r.score).toFixed(0)} / ${outcome} / ${Number(r.duration_seconds ?? 0)}s`;
};

const lines = [
  '# Application Benchmark',
  '',
  '| Task | Family | Weight | ' + efforts.join(' | ') + ' |',
  '|---|---|---:|' + efforts.map(() => '---').join('|') + '|',
];
for (const family of manifest.families) {
  lines.push(`| ${family.id} | ${family.family} | ${family.weight} | ${efforts.map((e) => cellFor(family, e)).join(' | ')} |`);
}

lines.push(
  '',
  '## Overall',
  '',
  '| Effort | Quality | Budget completion | Practical score | Runtime | Input tokens | Reasoning tokens | Data |',
  '|---|---:|---:|---:|---:|---:|---:|---|',
);
for (const effort of efforts) {
  const s = byEffort[effort];
  lines.push(
    `| ${effort} | ${s.quality_score == null ? '-' : s.quality_score.toFixed(1)} | ${pct(s.budget_completion_rate)} | ${s.practical_score == null ? '-' : s.practical_score.toFixed(1)} | ${s.duration_seconds}s | ${fmt(s.input_tokens)} | ${fmt(s.reasoning_tokens)} | ${s.data_complete ? '完整' : '不完整：' + s.incomplete_tasks.join(', ')} |`
  );
}

lines.push(
  '',
  '> Quality = hidden-checkpoint score. Practical score = 85% quality + 15% budget-completion reliability. Infrastructure/API failures are marked incomplete and excluded instead of being scored as model failures.',
  ''
);

fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
