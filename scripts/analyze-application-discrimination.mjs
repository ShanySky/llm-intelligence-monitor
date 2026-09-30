import fs from 'node:fs';

const input = process.argv[2] ?? 'results/application-final-summary.json';
const policyPath = process.argv[3] ?? 'benchmarks/application-selection-policy.json';
const outJson = process.argv[4] ?? 'results/application-discrimination.json';
const outMd = process.argv[5] ?? 'results/application-discrimination.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const registryPath = 'benchmarks/frontier-registry.json';
let frontierRegistry = { tasks: [] };
if (fs.existsSync(registryPath)) {
  try { frontierRegistry = JSON.parse(fs.readFileSync(registryPath, 'utf8')); } catch {}
}
const registryByTask = new Map((frontierRegistry.tasks ?? []).map((x) => [x.id, x]));
const residentSolModel = frontierRegistry.resident_model_epoch?.resident_sol_model ?? null;
const rows = Array.isArray(data.rows) ? data.rows : [];
const families = data.manifest?.families ?? [];
if (!rows.length) throw new Error('No result rows found');

const q = policy.quality ?? {};
const runtime = policy.runtime ?? {};
const efficiency = policy.efficiency ?? {};
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
    average_shell_commands: mean(xs.map(x=>Number(x.shell_commands ?? 0))),
    average_input_tokens: mean(xs.map(x=>Number(x.usage?.input_tokens ?? 0))),
    average_output_tokens: mean(xs.map(x=>Number(x.usage?.output_tokens ?? 0))),
    average_total_tokens: mean(xs.map(x=>Number(
      x.usage?.total_tokens ??
      (Number(x.usage?.input_tokens ?? 0) + Number(x.usage?.output_tokens ?? 0))
    ))),
    average_reasoning_tokens: mean(xs.map(x=>Number(x.usage?.reasoning_tokens ?? 0))),
  }));

  const xhighModels = configStats.filter((x) => x.effort === 'xhigh');
  const xhighScores = xhighModels.map((x) => x.average_score).filter(Number.isFinite);
  const solEfforts = configStats
    .filter((x) => x.model === 'gpt-6.1-sol' || x.model === 'gpt-6-sol')
    .sort((a,b)=>(effortRank[a.effort]??99)-(effortRank[b.effort]??99));
  const solScores = solEfforts.map((x) => x.average_score).filter(Number.isFinite);

  const modelSpread = range(xhighScores);
  const effortSpread = range(solScores);
  const solMedium = solEfforts.find((x) => x.effort === 'medium') ?? null;
  const solHigh = solEfforts.find((x) => x.effort === 'high') ?? null;
  const solXhigh = solEfforts.find((x) => x.effort === 'xhigh') ?? null;
  const directionalEffortGain =
    solMedium && solXhigh ? solXhigh.average_score - solMedium.average_score : null;
  const minEffortTrials = Math.min(
    ...solEfforts.filter((x) => ['medium','high','xhigh'].includes(x.effort)).map((x) => x.trials),
    Infinity
  );
  const maxStd = configStats.length ? Math.max(...configStats.map((x)=>x.stddev_score ?? 0)) : null;
  const ceilingConfigs = configStats.filter((x) => x.average_score >= Number(q.ceiling_score ?? 95)).length;
  const ceilingRate = configStats.length ? ceilingConfigs/configStats.length : null;
  const maxDuration = configStats.length ? Math.max(...configStats.map((x)=>x.average_duration_seconds ?? 0)) : null;

  const stable = maxStd == null || maxStd <= Number(q.max_repeat_stddev_points ?? 12);
  const withinBudget = maxDuration == null || maxDuration <= Number(runtime.hard_limit_seconds ?? 600);
  const registryEvidence = registryByTask.get(family.id) ?? null;
  const registryModelConfirmed = Boolean(
    registryEvidence?.promoted_to_final &&
    ['model-discriminator-confirmed','model+effort-discriminator-confirmed'].includes(registryEvidence?.status)
  );
  const registryEffortConfirmed = Boolean(
    ['effort-discriminator-confirmed','model+effort-discriminator-confirmed'].includes(registryEvidence?.status)
  );
  const repeatedModelEvidence = configStats.length > 0 && configStats.every((x) => x.trials >= 2);
  const modelDiscriminatorCurrent =
    modelSpread != null &&
    modelSpread >= Number(q.min_model_spread_points ?? 10) &&
    repeatedModelEvidence;
  const modelDiscriminator = registryModelConfirmed || modelDiscriminatorCurrent;
  const effortCandidate =
    directionalEffortGain != null &&
    directionalEffortGain >= Number(q.min_effort_directional_gain_points ?? q.min_effort_spread_points ?? 10);
  const repeatEnough =
    Number.isFinite(minEffortTrials) &&
    minEffortTrials >= Number(q.min_trials_for_effort_confirmation ?? 2);
  const effortDiscriminator = registryEffortConfirmed || (effortCandidate && repeatEnough && stable);

  const efficiencyFloor = Number(efficiency.min_quality_floor ?? 95);
  const minEfficiencyImprovement = Number(efficiency.min_improvement_percent ?? 15) / 100;
  const minImprovedMetrics = Number(efficiency.min_improved_metrics ?? 2);
  const efficiencyMetrics = [];
  if (solMedium && solXhigh &&
      solMedium.average_score >= efficiencyFloor &&
      solXhigh.average_score >= efficiencyFloor) {
    const candidates = [
      ['duration_seconds', solMedium.average_duration_seconds, solXhigh.average_duration_seconds],
      ['shell_commands', solMedium.average_shell_commands, solXhigh.average_shell_commands],
      ['total_tokens', solMedium.average_total_tokens, solXhigh.average_total_tokens],
    ];
    for (const [metric, mediumValue, xhighValue] of candidates) {
      if (Number.isFinite(mediumValue) && mediumValue > 0 && Number.isFinite(xhighValue)) {
        const improvement = (mediumValue - xhighValue) / mediumValue;
        if (improvement >= minEfficiencyImprovement) {
          efficiencyMetrics.push({
            metric,
            medium: mediumValue,
            xhigh: xhighValue,
            improvement_percent: improvement * 100,
          });
        }
      }
    }
  }
  const efficiencyCandidate = efficiencyMetrics.length >= minImprovedMetrics;

  let classification;
  if (!withinBudget) classification = 'too-slow';
  else if (!stable) classification = 'noisy';
  else if (modelDiscriminator && effortDiscriminator) classification = 'model+effort-discriminator';
  else if (effortDiscriminator) classification = 'effort-discriminator';
  else if (modelDiscriminator && effortCandidate) classification = 'model+effort-candidate';
  else if (effortCandidate) classification = 'effort-candidate';
  else if (modelDiscriminator) classification = 'model-discriminator';
  else if (ceilingRate != null && ceilingRate >= 0.8) classification = 'coverage-only-ceiling';
  else classification = 'coverage-or-needs-more-data';

  tasks.push({
    task: family.id,
    family: family.family,
    role: family.role ?? 'coverage',
    weight: family.weight,
    classification,
    model_spread_points: modelSpread,
    model_signal_confirmed: modelDiscriminator,
    model_signal_source: registryModelConfirmed ? 'registry-repeat-validation' : (modelDiscriminatorCurrent ? 'current-repeated-run' : 'unconfirmed'),
    effort_signal_confirmed: effortDiscriminator,
    effort_signal_source: registryEffortConfirmed ? 'registry-repeat-validation' : (effortDiscriminator ? 'current-repeated-run' : 'unconfirmed'),
    sol_effort_spread_points: effortSpread,
    sol_directional_effort_gain_points: directionalEffortGain,
    min_sol_effort_trials: Number.isFinite(minEffortTrials) ? minEffortTrials : null,
    max_repeat_stddev_points: maxStd,
    ceiling_rate: ceilingRate,
    max_average_duration_seconds: maxDuration,
    efficiency_candidate: efficiencyCandidate,
    efficiency_improved_metrics: efficiencyMetrics,
    stable,
    within_budget: withinBudget,
    config_stats: configStats,
  });
}

const coreTasks = tasks.filter((x) => x.role === 'core');
const confirmedModelCoreTasks = coreTasks.filter((x) => x.model_signal_confirmed);
const confirmedEffortRegistryTasks = (frontierRegistry.tasks ?? []).filter((x) =>
  ['effort-discriminator-confirmed','model+effort-discriminator-confirmed','effort-sensitivity-confirmed'].includes(x?.status) &&
  (!residentSolModel || x?.evidence?.resident_sol_model === residentSolModel)
);
const minModelCoreFamilies = Number(policy.selection?.model_core_min_families ?? data.manifest?.core_min_families_for_mature_score ?? 2);
const minEffortCoreFamilies = Number(policy.selection?.effort_core_min_families ?? 1);
const modelCoreMature = confirmedModelCoreTasks.length >= minModelCoreFamilies;
const effortCoreMature = confirmedEffortRegistryTasks.length >= minEffortCoreFamilies;

const output = {
  generated_at: new Date().toISOString(),
  policy,
  core_signal: {
    model_core: {
      configured_families: coreTasks.length,
      confirmed_families: confirmedModelCoreTasks.length,
      minimum_families: minModelCoreFamilies,
      mature: modelCoreMature,
      confirmed_tasks: confirmedModelCoreTasks.map((x) => x.task),
    },
    effort_core: {
      resident_sol_model: residentSolModel,
      confirmed_families: confirmedEffortRegistryTasks.length,
      minimum_families: minEffortCoreFamilies,
      mature: effortCoreMature,
      confirmed_tasks: confirmedEffortRegistryTasks.map((x) => x.id),
    },
    mature: modelCoreMature && effortCoreMature,
  },
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
  '| Task | Family | Role | Class | Model signal | XHigh model spread | Sol M→XH gain | Effort signal | Efficiency signal | Min effort trials | Repeat stddev | Ceiling rate | Max avg runtime |',
  '|---|---|---|---|---|---:|---:|---|---|---:|---:|---:|---:|',
];
for (const x of tasks) {
  const eff = x.efficiency_candidate
    ? x.efficiency_improved_metrics.map(m=>`${m.metric} ${m.improvement_percent.toFixed(0)}%`).join(', ')
    : '-';
  lines.push(`| ${x.task} | ${x.family} | ${x.role} | ${x.classification} | ${x.model_signal_confirmed ? 'confirmed' : 'unconfirmed'} | ${f1(x.model_spread_points)} | ${f1(x.sol_directional_effort_gain_points)} | ${x.effort_signal_confirmed ? 'confirmed' : 'unconfirmed'} | ${eff} | ${x.min_sol_effort_trials ?? '-'} | ${f1(x.max_repeat_stddev_points)} | ${pct(x.ceiling_rate)} | ${x.max_average_duration_seconds == null ? '-' : Math.round(x.max_average_duration_seconds)+'s'} |`);
}
lines.push(
  '',
  `**Model Core:** ${output.core_signal.model_core.confirmed_families}/${output.core_signal.model_core.minimum_families} → ${output.core_signal.model_core.mature ? 'mature' : 'not yet mature'}; **Effort Core:** ${output.core_signal.effort_core.confirmed_families}/${output.core_signal.effort_core.minimum_families} → ${output.core_signal.effort_core.mature ? 'mature' : 'not yet mature'}; **Overall application maturity:** ${output.core_signal.mature ? 'mature' : 'not yet mature'}.`,
  '',
  '> Selection rule: formal model/effort promotion requires repeated evidence. A one-shot spread in the final suite is diagnostic only; previously repeated frontier validation recorded in the registry remains the authoritative promotion evidence. Quality discrimination and execution efficiency are separate signals. Effort discrimination requires a repeated positive Medium→X High quality gain. A ceiling task may additionally show an efficiency candidate when X High uses materially less runtime/tool work/token cost at the same quality, but that does not count as a quality win and still requires repeated validation.',
  ''
);
fs.writeFileSync(outMd, lines.join('\n'));
console.log(lines.join('\n'));
