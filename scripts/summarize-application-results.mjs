import fs from 'node:fs';
import path from 'node:path';

const dir = process.argv[2] ?? 'results/application';
const manifestPath = process.argv[3] ?? 'benchmarks/application-suite.json';
const outJson = process.argv[4] ?? 'results/application-summary.json';
const outMd = process.argv[5] ?? 'results/application-summary.md';
const priorPath = process.argv[6] ?? '';

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const weights = Object.fromEntries(manifest.families.map((x) => [x.id, Number(x.weight)]));

const currentRows = [];
function walk(p) {
  for (const ent of fs.readdirSync(p, { withFileTypes: true })) {
    const full = path.join(p, ent.name);
    if (ent.isDirectory()) walk(full);
    else if (ent.name === 'result.json') {
      try { currentRows.push(JSON.parse(fs.readFileSync(full, 'utf8'))); } catch {}
    }
  }
}
if (fs.existsSync(dir)) walk(dir);

let priorRows = [];
if (priorPath && fs.existsSync(priorPath)) {
  try { priorRows = JSON.parse(fs.readFileSync(priorPath, 'utf8'))?.rows ?? []; } catch {}
}
if (!currentRows.length && !priorRows.length) throw new Error('No application benchmark result rows found');

const normalizeModel = (r) => String(r.model ?? 'unknown-model');
const normalizeEffort = (r) => String(r.effort ?? 'unknown');
const configKey = (r) => `${normalizeModel(r)}|${normalizeEffort(r)}`;

const merged = new Map();
for (const r of priorRows) merged.set(`${r.task}|${configKey(r)}`, r);
for (const r of currentRows) {
  const key = `${r.task}|${configKey(r)}`;
  const prior = merged.get(key);
  const currentComplete = typeof r.data_complete === 'boolean' ? r.data_complete : !r.infrastructure_error;
  const priorComplete = prior && (typeof prior.data_complete === 'boolean' ? prior.data_complete : !prior.infrastructure_error);
  if (currentComplete || !priorComplete) merged.set(key, r);
}
const rows = [...merged.values()];

function rowDataComplete(r) {
  if (typeof r.data_complete === 'boolean') return r.data_complete;
  return !r.infrastructure_error;
}

const effortRank = { low: 0, medium: 1, high: 2, xhigh: 3 };
const configMap = new Map();
for (const r of rows) {
  const key = configKey(r);
  if (!configMap.has(key)) configMap.set(key, { key, model: normalizeModel(r), effort: normalizeEffort(r) });
}
const configs = [...configMap.values()].sort((a, b) =>
  a.model.localeCompare(b.model) ||
  ((effortRank[a.effort] ?? 99) - (effortRank[b.effort] ?? 99)) ||
  a.effort.localeCompare(b.effort)
);

const totalWeight = manifest.families.reduce((s, x) => s + Number(x.weight), 0);
const byConfig = {};

for (const cfg of configs) {
  const rs = rows.filter((r) => configKey(r) === cfg.key);
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

  const durationSeconds = valid.reduce((s, r) => s + Number(r.duration_seconds ?? 0), 0);
  const inputTokens = valid.reduce((s, r) => s + Number(r.usage?.input_tokens ?? 0), 0);
  const outputTokens = valid.reduce((s, r) => s + Number(r.usage?.output_tokens ?? 0), 0);
  const reasoningTokens = valid.reduce((s, r) => s + Number(r.usage?.reasoning_tokens ?? 0), 0);
  const taskCount = valid.length;

  byConfig[cfg.key] = {
    model: cfg.model,
    effort: cfg.effort,
    data_complete: validWeight === totalWeight,
    valid_weight: validWeight,
    total_weight: totalWeight,
    task_count: taskCount,
    quality_score: validWeight ? qualityWeighted / validWeight : null,
    practical_score: validWeight ? practicalWeighted / validWeight : null,
    budget_completion_rate: valid.length ? completeTasks.length / valid.length : null,
    duration_seconds: durationSeconds,
    average_duration_seconds: taskCount ? durationSeconds / taskCount : null,
    input_tokens: inputTokens,
    output_tokens: outputTokens,
    reasoning_tokens: reasoningTokens,
    average_input_tokens: taskCount ? inputTokens / taskCount : null,
    average_reasoning_tokens: taskCount ? reasoningTokens / taskCount : null,
    api_retries: rs.reduce((s, r) => s + Number(r.api_retries ?? 0), 0),
    incomplete_tasks: rs.filter((r) => !rowDataComplete(r)).map((r) => r.task),
  };
}

const uniqueModels = [...new Set(configs.map((c) => c.model))];
const byEffort = {};
if (uniqueModels.length === 1) {
  for (const cfg of configs) byEffort[cfg.effort] = byConfig[cfg.key];
}

const summary = {
  generated_at: new Date().toISOString(),
  manifest,
  configs,
  rows,
  by_config: byConfig,
  by_effort: byEffort,
};
fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, JSON.stringify(summary, null, 2) + '\n');

const fmt = (n) => n == null ? '-' : Number(n).toLocaleString('en-US');
const pct = (n) => n == null ? '-' : (Number(n) * 100).toFixed(0) + '%';
const cfgLabel = (cfg) => `${cfg.model} / ${cfg.effort}`;

function cellFor(family, cfg) {
  const r = rows.find((x) => x.task === family.id && configKey(x) === cfg.key);
  if (!r) return '-';
  if (!rowDataComplete(r)) return '数据不完整';
  const outcome = r.outcome === 'model_timeout' ? '超时' : '完成';
  return `${Number(r.score).toFixed(0)} / ${outcome} / ${Number(r.duration_seconds ?? 0)}s`;
}

const lines = [
  '# Application Benchmark',
  '',
  '| Task | Family | Weight | ' + configs.map(cfgLabel).join(' | ') + ' |',
  '|---|---|---:|' + configs.map(() => '---').join('|') + '|',
];
for (const family of manifest.families) {
  lines.push(`| ${family.id} | ${family.family} | ${family.weight} | ${configs.map((c) => cellFor(family, c)).join(' | ')} |`);
}

lines.push(
  '',
  '## Overall',
  '',
  '| Model | Effort | Quality | Budget completion | Practical | Runtime | Avg/task | Input tokens | Reasoning tokens | Data |',
  '|---|---|---:|---:|---:|---:|---:|---:|---:|---|',
);
for (const cfg of configs) {
  const s = byConfig[cfg.key];
  lines.push(
    `| ${cfg.model} | ${cfg.effort} | ${s.quality_score == null ? '-' : s.quality_score.toFixed(1)} | ${pct(s.budget_completion_rate)} | ${s.practical_score == null ? '-' : s.practical_score.toFixed(1)} | ${s.duration_seconds}s | ${s.average_duration_seconds == null ? '-' : s.average_duration_seconds.toFixed(0) + 's'} | ${fmt(s.input_tokens)} | ${fmt(s.reasoning_tokens)} | ${s.data_complete ? '完整' : '不完整：' + s.incomplete_tasks.join(', ')} |`
  );
}

lines.push(
  '',
  '> Quality = hidden-checkpoint score. Practical = 85% quality + 15% budget-completion reliability. Runtime and token usage are reported separately and are not silently folded into intelligence quality. Infrastructure/API failures are marked incomplete instead of being scored as model failures.',
  ''
);

fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
