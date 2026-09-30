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

const mean = (xs) => xs.length ? xs.reduce((a,b)=>a+b,0)/xs.length : null;
const stdev = (xs) => {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((s,x)=>s+(x-m)**2,0)/xs.length);
};
const totalTokens = (r) =>
  Number(r?.usage?.total_tokens ??
    (Number(r?.usage?.input_tokens ?? 0) + Number(r?.usage?.output_tokens ?? 0)));

function stats(effort) {
  const xs = rows.filter((r) => r.effort === effort);
  const valid = xs.filter((r) => r.data_complete !== false && !r.infrastructure_error);
  if (!xs.length) return null;
  return {
    effort,
    trials: valid.length,
    expected_trials: xs.length,
    score: mean(valid.map(r=>Number(r.score ?? 0))),
    score_stddev: stdev(valid.map(r=>Number(r.score ?? 0))),
    duration_seconds: mean(valid.map(r=>Number(r.duration_seconds ?? 0))),
    shell_commands: mean(valid.map(r=>Number(r.shell_commands ?? 0))),
    probe_calls: mean(valid.map(r=>Number(r.probe_calls ?? 0))),
    probe_attempts: mean(valid.map(r=>Number(r.probe_attempts ?? r.probe_calls ?? 0))),
    total_tokens: mean(valid.map(totalTokens)),
    reasoning_tokens: mean(valid.map(r=>Number(r?.usage?.reasoning_tokens ?? 0))),
    saturated: valid.some(r=>Boolean(r.turn_limit_reached || r.shell_budget_reached)),
    data_complete: valid.length === xs.length,
  };
}

const byEffort = Object.fromEntries(
  ['medium','high','xhigh']
    .map((e)=>[e,stats(e)])
    .filter(([,v])=>v)
);
const medium = byEffort.medium ?? null;
const high = byEffort.high ?? null;
const xhigh = byEffort.xhigh ?? null;

const trialMap = (effort) => new Map(
  rows
    .filter((r)=>r.effort===effort && r.data_complete !== false && !r.infrastructure_error)
    .map((r,i)=>[Number(r.trial ?? (i+1)),r])
);
const mTrials = trialMap('medium');
const xTrials = trialMap('xhigh');
const commonTrials = [...mTrials.keys()].filter((t)=>xTrials.has(t)).sort((a,b)=>a-b);

const pctImprovement = (baseline, candidate) => {
  if (!Number.isFinite(baseline) || baseline <= 0 || !Number.isFinite(candidate)) return null;
  return ((baseline - candidate) / baseline) * 100;
};

const minQualityGain = Number(quality.min_effort_directional_gain_points ?? 10);
const minTrials = Number(quality.min_trials_for_effort_confirmation ?? 2);
const maxStd = Number(quality.max_repeat_stddev_points ?? 12);
const consistencyThreshold = Number(quality.min_directional_consistency_rate ?? 0.67);
const qualityFloor = Number(eff.min_quality_floor ?? 95);
const efficiencyThreshold = Number(eff.min_improvement_percent ?? 15);
const minEfficiencyMetrics = Number(eff.min_improved_metrics ?? 2);

let comparison = null;
if (medium && xhigh) {
  const improvements = {
    duration_seconds: pctImprovement(medium.duration_seconds, xhigh.duration_seconds),
    shell_commands: pctImprovement(medium.shell_commands, xhigh.shell_commands),
    probe_calls: pctImprovement(medium.probe_calls, xhigh.probe_calls),
    total_tokens: pctImprovement(medium.total_tokens, xhigh.total_tokens),
  };
  const improvedMetrics = Object.entries(improvements)
    .filter(([,v]) => v != null && v >= efficiencyThreshold)
    .map(([k]) => k);
  const qualityGain = xhigh.score - medium.score;

  const paired = commonTrials.map((trial)=>{
    const m=mTrials.get(trial), x=xTrials.get(trial);
    const pairImprovements = {
      duration_seconds: pctImprovement(Number(m.duration_seconds??0),Number(x.duration_seconds??0)),
      shell_commands: pctImprovement(Number(m.shell_commands??0),Number(x.shell_commands??0)),
      probe_calls: pctImprovement(Number(m.probe_calls??0),Number(x.probe_calls??0)),
      total_tokens: pctImprovement(totalTokens(m),totalTokens(x)),
    };
    const pairImprovedMetrics = Object.entries(pairImprovements)
      .filter(([,v])=>v!=null && v>=efficiencyThreshold)
      .map(([k])=>k);
    return {
      trial,
      medium_score:Number(m.score??0),
      xhigh_score:Number(x.score??0),
      quality_gain:Number(x.score??0)-Number(m.score??0),
      efficiency_improved_metrics:pairImprovedMetrics,
      efficiency_signal:
        Number(m.score??0)>=qualityFloor &&
        Number(x.score??0)>=qualityFloor &&
        Number(x.score??0)>=Number(m.score??0) &&
        pairImprovedMetrics.length>=minEfficiencyMetrics,
    };
  });

  const positiveQualityRate = paired.length
    ? paired.filter(p=>p.quality_gain>=minQualityGain).length/paired.length : 0;
  const efficiencyRate = paired.length
    ? paired.filter(p=>p.efficiency_signal).length/paired.length : 0;

  const enoughRepeats = commonTrials.length >= minTrials;
  const stable =
    medium.score_stddev <= maxStd &&
    xhigh.score_stddev <= maxStd;
  const saturated = medium.saturated || xhigh.saturated;
  const complete = medium.data_complete && xhigh.data_complete;

  const qualityCandidate = qualityGain >= minQualityGain;
  const qualityConfirmed =
    qualityCandidate && enoughRepeats && stable &&
    positiveQualityRate >= consistencyThreshold;

  const efficiencyCandidate =
    medium.score >= qualityFloor &&
    xhigh.score >= qualityFloor &&
    xhigh.score >= medium.score &&
    improvedMetrics.length >= minEfficiencyMetrics;
  const efficiencyConfirmed =
    efficiencyCandidate && enoughRepeats &&
    efficiencyRate >= consistencyThreshold;

  let classification = 'needs-more-data';
  if (!complete) classification = 'incomplete-data';
  else if (saturated) classification = 'budget-confounded';
  else if (qualityConfirmed) classification = 'quality-effort-confirmed';
  else if (qualityCandidate) classification = 'quality-effort-candidate';
  else if (efficiencyConfirmed) classification = 'efficiency-effort-confirmed';
  else if (efficiencyCandidate) classification = 'efficiency-effort-candidate';
  else if (medium.score >= qualityFloor && xhigh.score >= qualityFloor) {
    classification = 'quality-ceiling-no-m-to-xh-signal';
  }

  comparison = {
    medium_to_xhigh_quality_gain_points: qualityGain,
    improvements_percent: improvements,
    improved_metrics: improvedMetrics,
    common_trials: commonTrials.length,
    positive_quality_trial_rate: positiveQualityRate,
    efficiency_signal_trial_rate: efficiencyRate,
    classification,
    repeated_confirmation_required: !(
      classification === 'quality-effort-confirmed' ||
      classification === 'efficiency-effort-confirmed'
    ),
    paired_trials: paired,
  };
}

const effortStats = [medium,high,xhigh].filter(Boolean);
const scores = effortStats.map(x=>x.score).filter(Number.isFinite);
const effortSpread = scores.length ? Math.max(...scores)-Math.min(...scores) : null;
let effortSensitivity = null;
if (effortStats.length >= 2 && effortSpread != null) {
  const repeated = Math.min(...effortStats.map(x=>x.trials)) >= minTrials;
  const stable = Math.max(...effortStats.map(x=>x.score_stddev)) <= maxStd;
  const saturated = effortStats.some(x=>x.saturated);
  const complete = effortStats.every(x=>x.data_complete);
  const threshold = Number(quality.min_effort_spread_points ?? 10);
  if (effortSpread >= threshold) {
    const sorted=[...effortStats].sort((a,b)=>b.score-a.score);
    const ordered=['medium','high','xhigh']
      .map(k=>byEffort[k])
      .filter(Boolean)
      .map(x=>x.score);
    const increasing=ordered.length>=2 && ordered.every((v,i)=>i===0 || v>=ordered[i-1]);
    const decreasing=ordered.length>=2 && ordered.every((v,i)=>i===0 || v<=ordered[i-1]);
    effortSensitivity={
      spread_points:effortSpread,
      best_effort:sorted[0]?.effort ?? null,
      worst_effort:sorted[sorted.length-1]?.effort ?? null,
      shape:increasing?'nondecreasing':(decreasing?'nonincreasing':'nonmonotonic'),
      repeated,
      stable,
      saturated,
      data_complete:complete,
      classification:
        complete && !saturated && repeated && stable
          ? 'effort-sensitivity-confirmed'
          : 'effort-sensitivity-candidate',
    };
  }
}

let nonMonotonic = null;
if (medium && high && xhigh) {
  const highDip = Math.min(medium.score,xhigh.score)-high.score;
  const highSpike = high.score-Math.max(medium.score,xhigh.score);
  const magnitude = Math.max(highDip,highSpike,0);
  const repeated = Math.min(medium.trials,high.trials,xhigh.trials) >= minTrials;
  const stable = Math.max(medium.score_stddev,high.score_stddev,xhigh.score_stddev) <= maxStd;
  if (magnitude >= Number(quality.min_effort_spread_points ?? 10)) {
    nonMonotonic = {
      direction: highDip >= highSpike ? 'high-dip' : 'high-spike',
      magnitude_points: magnitude,
      classification: repeated && stable
        ? 'nonmonotonic-effort-anomaly-confirmed'
        : 'nonmonotonic-effort-anomaly-candidate',
      repeated,
      stable,
    };
  }
}

const output = {
  generated_at: new Date().toISOString(),
  task: rows[0]?.task ?? null,
  model: rows[0]?.model ?? null,
  trial_count: Math.max(...Object.values(byEffort).map(x=>x.trials),0),
  by_effort: byEffort,
  effort_spread_points: effortSpread,
  medium_to_xhigh: comparison,
  effort_sensitivity: effortSensitivity,
  nonmonotonic: nonMonotonic,
};
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const f1 = (v) => v == null ? '-' : Number(v).toFixed(1);
const lines = [
  '# Frontier Effort Analysis',
  '',
  '| Effort | Trials | Quality mean | Quality stddev | Runtime avg | Shell avg | Probes avg | Probe attempts avg | Total tokens avg | Reasoning avg | Saturated |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
];
for (const key of ['medium','high','xhigh']) {
  const r = byEffort[key];
  if (!r) continue;
  lines.push(`| ${key} | ${r.trials} | ${f1(r.score)} | ${f1(r.score_stddev)} | ${Math.round(r.duration_seconds??0)}s | ${f1(r.shell_commands)} | ${f1(r.probe_calls)} | ${f1(r.probe_attempts)} | ${Math.round(r.total_tokens??0)} | ${Math.round(r.reasoning_tokens??0)} | ${r.saturated ? 'yes' : 'no'} |`);
}
if (comparison) {
  lines.push(
    '',
    `**M→XH classification:** \`${comparison.classification}\``,
    '',
    `Quality gain: ${f1(comparison.medium_to_xhigh_quality_gain_points)} points; ` +
    `runtime improvement: ${f1(comparison.improvements_percent.duration_seconds)}%; ` +
    `shell improvement: ${f1(comparison.improvements_percent.shell_commands)}%; ` +
    `probe improvement: ${f1(comparison.improvements_percent.probe_calls)}%; ` +
    `token improvement: ${f1(comparison.improvements_percent.total_tokens)}%; ` +
    `paired trials: ${comparison.common_trials}.`,
  );
}
if (effortSensitivity) {
  lines.push(
    '',
    `**Effort sensitivity:** \`${effortSensitivity.classification}\` (spread ${f1(effortSensitivity.spread_points)} points; best=${effortSensitivity.best_effort}; worst=${effortSensitivity.worst_effort}; shape=${effortSensitivity.shape}).`,
  );
}
if (nonMonotonic) {
  lines.push(
    '',
    `**Non-monotonic signal:** \`${nonMonotonic.classification}\` (${nonMonotonic.direction}, ${f1(nonMonotonic.magnitude_points)} points).`,
  );
}
lines.push(
  '',
  '> Directional quality improvement, generic effort sensitivity, efficiency, and non-monotonic anomalies are separate signals. Effort sensitivity means the chosen effort level reliably changes quality; it does not imply that higher effort is better. Formal effort-discriminator promotion still requires repeated positive Medium→X High quality gain.',
);
fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
