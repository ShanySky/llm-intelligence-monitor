import fs from 'node:fs';
import path from 'node:path';

const dir = process.argv[2] ?? 'results/repeated';
const outJson = process.argv[3] ?? 'results/repeated-summary.json';
const outMd = process.argv[4] ?? 'results/repeated-summary.md';

const rows = [];
function walk(p) {
  if (!fs.existsSync(p)) return;
  for (const ent of fs.readdirSync(p, { withFileTypes: true })) {
    const full = path.join(p, ent.name);
    if (ent.isDirectory()) walk(full);
    else if (ent.name === 'result.json') {
      try { rows.push(JSON.parse(fs.readFileSync(full, 'utf8'))); } catch {}
    }
  }
}
walk(dir);
if (!rows.length) throw new Error('No repeated benchmark rows found');

const effortOrder = ['medium', 'high', 'xhigh'];
const efforts = effortOrder.filter((e) => rows.some((r) => r.effort === e));

function avg(xs) {
  const vals = xs.filter(Number.isFinite);
  return vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : null;
}
function min(xs) {
  const vals = xs.filter(Number.isFinite);
  return vals.length ? Math.min(...vals) : null;
}
function max(xs) {
  const vals = xs.filter(Number.isFinite);
  return vals.length ? Math.max(...vals) : null;
}

const byEffort = {};
for (const effort of efforts) {
  const rs = rows.filter((r) => r.effort === effort && r.data_complete !== false);
  const checkNames = [...new Set(rs.flatMap((r) => Object.keys(r.checks ?? {})))].sort();
  const checks = {};
  for (const name of checkNames) {
    const vals = rs.map((r) => r.checks?.[name]?.passed).filter((x) => typeof x === 'boolean');
    checks[name] = {
      passed: vals.filter(Boolean).length,
      total: vals.length,
      rate: vals.length ? vals.filter(Boolean).length / vals.length : null,
    };
  }
  const scores = rs.map((r) => Number(r.score));
  byEffort[effort] = {
    trials: rs.length,
    average_score: avg(scores),
    min_score: min(scores),
    max_score: max(scores),
    average_duration_seconds: avg(rs.map((r) => Number(r.duration_seconds))),
    average_input_tokens: avg(rs.map((r) => Number(r.usage?.input_tokens))),
    average_reasoning_tokens: avg(rs.map((r) => Number(r.usage?.reasoning_tokens))),
    checks,
  };
}

const summary = { generated_at: new Date().toISOString(), rows, by_effort: byEffort };
fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(summary, null, 2) + '\n');

const fmt = (n, d=1) => n == null ? '-' : Number(n).toFixed(d);
const lines = [
  '# Repeated Application Validation',
  '',
  '| Effort | Trials | Avg score | Range | Avg runtime | Avg input tokens | Avg reasoning tokens |',
  '|---|---:|---:|---:|---:|---:|---:|',
];
for (const effort of efforts) {
  const s = byEffort[effort];
  lines.push(`| ${effort} | ${s.trials} | ${fmt(s.average_score)} | ${fmt(s.min_score,0)}–${fmt(s.max_score,0)} | ${fmt(s.average_duration_seconds,0)}s | ${fmt(s.average_input_tokens,0)} | ${fmt(s.average_reasoning_tokens,0)} |`);
}

const allChecks = [...new Set(efforts.flatMap((e) => Object.keys(byEffort[e].checks)))].sort();
lines.push('', '## Check pass rates', '', '| Check | ' + efforts.join(' | ') + ' |', '|---|' + efforts.map(()=> '---:').join('|') + '|');
for (const name of allChecks) {
  lines.push('| ' + name + ' | ' + efforts.map((e) => {
    const c = byEffort[e].checks[name];
    return c && c.total ? `${c.passed}/${c.total}` : '-';
  }).join(' | ') + ' |');
}

lines.push('', '## Individual runs', '', '| Effort | Trial | Score | Runtime | Input tokens | Reasoning tokens |', '|---|---:|---:|---:|---:|---:|');
for (const r of rows.sort((a,b) => effortOrder.indexOf(a.effort)-effortOrder.indexOf(b.effort) || Number(a.trial)-Number(b.trial))) {
  lines.push(`| ${r.effort} | ${r.trial ?? '-'} | ${r.score} | ${r.duration_seconds}s | ${r.usage?.input_tokens ?? 0} | ${r.usage?.reasoning_tokens ?? 0} |`);
}
lines.push('');
fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
