import fs from 'node:fs';

const input = process.argv[2] ?? 'results/frontier-effort-summary.json';
const policyPath = process.argv[3] ?? 'benchmarks/application-selection-policy.json';
const outJson = process.argv[4] ?? 'results/frontier-effort-analysis.json';
const outMd = process.argv[5] ?? 'results/frontier-effort-analysis.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const rows = Array.isArray(data.rows) ? data.rows : [];
const eff = policy.efficiency ?? {};
const quality = policy.quality ?? {};

const totalTokens = (r) =>
  Number(r?.usage?.input_tokens ?? 0) + Number(r?.usage?.output_tokens ?? 0);

const byEffort = Object.fromEntries(rows.map((r) => [r.effort, {
  effort: r.effort,
  score: Number(r.score ?? 0),
  duration_seconds: Number(r.duration_seconds ?? 0),
  shell_commands: Number(r.shell_commands ?? 0),
  total_tokens: totalTokens(r),
  reasoning_tokens: Number(r?.usage?.reasoning_tokens ?? 0),
  saturated: Boolean(r.turn_limit_reached || r.shell_budget_reached),
  data_complete: r.data_complete !== false && !r.infrastructure_error,
}]));

const medium = byEffort.medium ?? null;
const high = byEffort.high ?? null;
const xhigh = byEffort.xhigh ?? null;
const pctImprovement = (baseline, candidate) => {
  if (!Number.isFinite(baseline) || baseline <= 0 || !Number.isFinite(candidate)) return null;
  return ((baseline - candidate) / baseline) * 100;
};

let comparison = null;
if (medium && xhigh) {
  const improvements = {
    duration_seconds: pctImprovement(medium.duration_seconds, xhigh.duration_seconds),
    shell_commands: pctImprovement(medium.shell_commands, xhigh.shell_commands),
    total_tokens: pctImprovement(medium.total_tokens, xhigh.total_tokens),
  };
  const threshold = Number(eff.min_improvement_percent ?? 15);
  const improvedMetrics = Object.entries(improvements)
    .filter(([,v]) => v != null && v >= threshold)
    .map(([k]) => k);
  const qualityGain = xhigh.score - medium.score;
  const qualityFloor = Number(eff.min_quality_floor ?? 95);
  const minMetrics = Number(eff.min_improved_metrics ?? 2);
  const saturated = medium.saturated || xhigh.saturated;
  let classification = 'needs-more-data';

  if (!medium.data_complete || !xhigh.data_complete) {
    classification = 'incomplete-data';
  } else if (saturated) {
    classification = 'budget-confounded';
  } else if (qualityGain >= Number(quality.min_effort_directional_gain_points ?? 10)) {
    classification = 'quality-effort-candidate';
  } else if (
    medium.score >= qualityFloor &&
    xhigh.score >= qualityFloor &&
    xhigh.score >= medium.score &&
    improvedMetrics.length >= minMetrics
  ) {
    classification = 'efficiency-effort-candidate';
  } else if (medium.score >= qualityFloor && xhigh.score >= qualityFloor) {
    classification = 'quality-ceiling-no-effort-signal';
  }

  comparison = {
    medium_to_xhigh_quality_gain_points: qualityGain,
    improvements_percent: improvements,
    improved_metrics: improvedMetrics,
    classification,
    repeated_confirmation_required: true,
  };
}

const output = {
  generated_at: new Date().toISOString(),
  task: rows[0]?.task ?? null,
  model: rows[0]?.model ?? null,
  by_effort: byEffort,
  medium_to_xhigh: comparison,
};
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const f1 = (v) => v == null ? '-' : Number(v).toFixed(1);
const lines = [
  '# Frontier Effort Analysis',
  '',
  '| Effort | Quality | Runtime | Shell | Total tokens | Reasoning | Saturated |',
  '|---|---:|---:|---:|---:|---:|---|',
];
for (const key of ['medium','high','xhigh']) {
  const r = byEffort[key];
  if (!r) continue;
  lines.push(`| ${key} | ${r.score} | ${r.duration_seconds}s | ${r.shell_commands} | ${r.total_tokens} | ${r.reasoning_tokens} | ${r.saturated ? 'yes' : 'no'} |`);
}
if (comparison) {
  lines.push(
    '',
    `**M→XH classification:** \`${comparison.classification}\``,
    '',
    `Quality gain: ${f1(comparison.medium_to_xhigh_quality_gain_points)} points; ` +
    `runtime improvement: ${f1(comparison.improvements_percent.duration_seconds)}%; ` +
    `shell improvement: ${f1(comparison.improvements_percent.shell_commands)}%; ` +
    `token improvement: ${f1(comparison.improvements_percent.total_tokens)}%.`,
    '',
    '> Efficiency is reported separately from quality. A single run is only a candidate signal; repeated directionally consistent runs are required for confirmation.',
  );
}
fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
