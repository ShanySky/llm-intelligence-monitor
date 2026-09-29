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
const tasks = manifest.families.map((x) => x.id);

const byEffort = {};
for (const effort of efforts) {
  const rs = rows.filter((r) => r.effort === effort);
  let weighted = 0;
  let weightSum = 0;
  for (const r of rs) {
    const w = weights[r.task] ?? 0;
    weighted += Number(r.score ?? 0) * w;
    weightSum += w;
  }
  byEffort[effort] = {
    score: weightSum ? weighted / weightSum : 0,
    duration_seconds: rs.reduce((s, r) => s + Number(r.duration_seconds ?? 0), 0),
    input_tokens: rs.reduce((s, r) => s + Number(r.usage?.input_tokens ?? 0), 0),
    output_tokens: rs.reduce((s, r) => s + Number(r.usage?.output_tokens ?? 0), 0),
    reasoning_tokens: rs.reduce((s, r) => s + Number(r.usage?.reasoning_tokens ?? 0), 0),
  };
}

const summary = { generated_at: new Date().toISOString(), manifest, rows, by_effort: byEffort };
fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(summary, null, 2) + '\n');

const fmt = (n) => Number(n ?? 0).toLocaleString('en-US');
const lines = [
  '# Application Benchmark',
  '',
  '| Task | Family | Weight | ' + efforts.join(' | ') + ' |',
  '|---|---|---:|' + efforts.map(() => '---:').join('|') + '|',
];
for (const family of manifest.families) {
  const cells = efforts.map((effort) => {
    const r = rows.find((x) => x.task === family.id && x.effort === effort);
    return r ? `${Number(r.score).toFixed(0)} (${Number(r.duration_seconds ?? 0)}s)` : '-';
  });
  lines.push(`| ${family.id} | ${family.family} | ${family.weight} | ${cells.join(' | ')} |`);
}
lines.push('', '## Weighted totals', '', '| Effort | Score | Runtime | Input tokens | Reasoning tokens |', '|---|---:|---:|---:|---:|');
for (const effort of efforts) {
  const s = byEffort[effort];
  lines.push(`| ${effort} | ${s.score.toFixed(1)} | ${s.duration_seconds}s | ${fmt(s.input_tokens)} | ${fmt(s.reasoning_tokens)} |`);
}
lines.push('', '> Scores are objective hidden-checkpoint scores. Runtime is agent execution time, not total GitHub job time.', '');
fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
