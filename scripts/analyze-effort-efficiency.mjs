import fs from 'node:fs';

const input = process.argv[2] ?? 'results/frontier-effort-summary.json';
const policyPath = process.argv[3] ?? 'benchmarks/application-selection-policy.json';
const outJson = process.argv[4] ?? 'results/frontier-effort-analysis.json';
const outMd = process.argv[5] ?? 'results/frontier-effort-analysis.md';

const data = JSON.parse(fs.readFileSync(input, 'utf8'));
const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8'));
const rows = Array.isArray(data.rows) ? data.rows : [];
const trialMode = String(data.trial_mode ?? 'repeats');
const models = new Set(rows.map(r=>String(r.model??'')).filter(Boolean));
if(models.size>1) {
  throw new Error('Mixed model epochs/configurations in effort analysis: '+[...models].join(', '));
}
const familyVersion=Number(data.family_version ?? 1);
if(rows.some(r=>r.family_version!=null && Number(r.family_version)!==familyVersion)) {
  throw new Error('Mixed real-repo replay family versions in one effort analysis');
}
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
    changed_files: mean(valid.map(r=>Number(r.patch_metrics?.changed_files ?? 0))),
    changed_lines: mean(valid.map(r=>Number(r.patch_metrics?.changed_lines ?? 0))),
    total_tokens: mean(valid.map(totalTokens)),
    reasoning_tokens: mean(valid.map(r=>Number(r?.usage?.reasoning_tokens ?? 0))),
    saturated: valid.some(r=>Boolean(r.turn_limit_reached || r.shell_budget_reached || r.model_timeout || r.outcome === 'model_timeout')),
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
const allTrialMaps = Object.fromEntries(
  ['medium','high','xhigh'].map((effort)=>[effort,trialMap(effort)])
);
const allTrialIds = [...new Set(
  Object.values(allTrialMaps).flatMap((m)=>[...m.keys()])
)].sort((a,b)=>a-b);

const pctImprovement = (baseline, candidate) => {
  if (!Number.isFinite(baseline) || baseline <= 0 || !Number.isFinite(candidate)) return null;
  return ((baseline - candidate) / baseline) * 100;
};

const minQualityGain = Number(quality.min_effort_directional_gain_points ?? 10);
const minTrials = Number(quality.min_trials_for_effort_confirmation ?? 2);
const maxStd = Number(quality.max_repeat_stddev_points ?? 12);
const consistencyThreshold = Number(quality.min_directional_consistency_rate ?? 0.67);
const familyMinVariants = Number(quality.effort_family_min_variants ?? 3);
const familyMinPositiveVariants = Number(quality.effort_family_min_positive_variants ?? 2);
const familyVariantGain = Number(quality.effort_family_variant_gain_points ?? minQualityGain);
const familyMinRepeatRounds = Math.max(2, Number(quality.effort_family_min_repeats_per_variant ?? 2));
// Distinct variants are not independent repeats. Formal variant-family confirmation
// requires an explicit repeat identifier for every config of each paired variant.
const hasPairedRepeatEvidence = (efforts, variants) =>
  variants.length >= familyMinVariants &&
  variants.every((trial) => efforts.every((effort) => {
    const xs=rows.filter(r=>r.effort===effort && Number(r.trial)===trial);
    const complete=xs.filter(r=>r.data_complete !== false && !r.infrastructure_error &&
      r.outcome !== 'model_timeout' && r.outcome !== 'pre_telemetry_timeout' &&
      !r.model_timeout && !r.turn_limit_reached && !r.shell_budget_reached);
    const repeats=new Set(complete.map(r=>r.repeat));
    return complete.length >= familyMinRepeatRounds &&
      !repeats.has(undefined) && repeats.size >= familyMinRepeatRounds;
  }));
const distinctVariants=[...new Set(rows.filter(r=>r.trial!=null).map(r=>Number(r.trial)))];

const repeatedVariantAgreement = (efforts, variants, threshold, direction='any') => {
  let agreed=0;
  const agreementBySignature=new Map();
  for (const trial of variants) {
    const configRounds=efforts.map(effort=>new Map(rows
      .filter(r=>r.effort===effort && Number(r.trial)===trial &&
        r.data_complete!==false && !r.infrastructure_error &&
        r.outcome!=='model_timeout' && r.outcome!=='pre_telemetry_timeout' &&
        !r.model_timeout && !r.turn_limit_reached && !r.shell_budget_reached &&
        r.repeat!=null)
      .map(r=>[String(r.repeat),r])));
    const common=[...configRounds[0].keys()].filter(k=>configRounds.every(m=>m.has(k)));
    if(common.length < familyMinRepeatRounds) continue;
    const signatures=[];
    let positive=0;
    for(const repeat of common){
      const values=configRounds.map(m=>Number(m.get(repeat).score));
      if(values.some(v=>!Number.isFinite(v))) continue;
      const spread=Math.max(...values)-Math.min(...values);
      if(spread<threshold) continue;
      const highIndex=values.indexOf(Math.max(...values));
      const lowIndex=values.indexOf(Math.min(...values));
      const signature=efforts[highIndex]+'>'+efforts[lowIndex];
      if(direction==='positive'){
        if(efforts.length===2 && values[1]-values[0]>=threshold) positive++;
      } else if(direction==='high-dip' || direction==='high-spike'){
        if(efforts.length!==3) continue;
        const [m,h,x]=values;
        const delta=direction==='high-dip'?Math.min(m,x)-h:h-Math.max(m,x);
        if(delta>=threshold) positive++;
      } else signatures.push(signature);
    }
    const required=Math.ceil(common.length*consistencyThreshold);
    if(direction==='any') {
      const winning=[...new Set(signatures)].find(s=>
        signatures.filter(x=>x===s).length>=required);
      if(winning) agreementBySignature.set(winning,(agreementBySignature.get(winning)??0)+1);
    } else if(positive>=required) {
      agreed++;
    }
  }
  // Cross-instance consistency matters too: two variants with opposite best/worst
  // effort directions cannot jointly establish a stable family-level sensitivity.
  return direction==='any'
    ? [...agreementBySignature.values()].some(n=>n>=familyMinPositiveVariants)
    : agreed>=familyMinPositiveVariants;
};

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

  const positiveQualityCount = paired.filter((p) =>
    p.quality_gain >= (trialMode === 'variants' ? familyVariantGain : minQualityGain)
  ).length;
  const positiveQualityRate = paired.length
    ? positiveQualityCount / paired.length : 0;
  const efficiencyRate = paired.length
    ? paired.filter(p=>p.efficiency_signal).length/paired.length : 0;

  const enoughRepeats = trialMode === 'variants'
    ? hasPairedRepeatEvidence(['medium','xhigh'],commonTrials)
    : commonTrials.length >= minTrials;
  const stable = trialMode === 'variants'
    ? true
    : (
      medium.score_stddev <= maxStd &&
      xhigh.score_stddev <= maxStd
    );
  const saturated = medium.saturated || xhigh.saturated;
  const complete = medium.data_complete && xhigh.data_complete;

  const qualityCandidate = qualityGain >= minQualityGain;
  const qualityConfirmed =
    qualityCandidate && enoughRepeats && stable &&
    (trialMode === 'variants'
      ? repeatedVariantAgreement(['medium','xhigh'],commonTrials,familyVariantGain,'positive')
      : positiveQualityRate >= consistencyThreshold);

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
    positive_quality_trial_count: positiveQualityCount,
    required_positive_trial_count: trialMode === 'variants' ? familyMinPositiveVariants : null,
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
  const threshold = Number(quality.min_effort_spread_points ?? 10);
  const repeated = trialMode === 'variants'
    ? hasPairedRepeatEvidence(effortStats.map(x=>x.effort),distinctVariants)
    : Math.min(...effortStats.map(x=>x.trials)) >= minTrials;
  const stable = trialMode === 'variants'
    ? true
    : Math.max(...effortStats.map(x=>x.score_stddev)) <= maxStd;
  const saturated = effortStats.some(x=>x.saturated);
  const complete = effortStats.every(x=>x.data_complete);

  const variantSensitivity = allTrialIds.map((trial)=>{
    const values=['medium','high','xhigh']
      .map((effort)=>allTrialMaps[effort].get(trial))
      .filter(Boolean)
      .map((row)=>Number(row.score??0));
    const spread=values.length>=2?Math.max(...values)-Math.min(...values):0;
    return {trial,spread_points:spread,sensitive:spread>=threshold};
  });
  const sensitiveVariantCount=variantSensitivity.filter(x=>x.sensitive).length;
  const variantConsistencyOk = trialMode !== 'variants' ||
    repeatedVariantAgreement(effortStats.map(x=>x.effort),distinctVariants,threshold);

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
      sensitive_variant_count:sensitiveVariantCount,
      required_sensitive_variant_count:trialMode==='variants'?familyMinPositiveVariants:null,
      variant_sensitivity:trialMode==='variants'?variantSensitivity:undefined,
      classification:
        complete && !saturated && repeated && stable && variantConsistencyOk
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
  const repeated = trialMode === 'variants'
    ? hasPairedRepeatEvidence(['medium','high','xhigh'],distinctVariants)
    : Math.min(medium.trials,high.trials,xhigh.trials) >= minTrials;
  const stable = trialMode === 'variants'
    ? true
    : Math.max(medium.score_stddev,high.score_stddev,xhigh.score_stddev) <= maxStd;
  if (magnitude >= Number(quality.min_effort_spread_points ?? 10)) {
    const direction=highDip >= highSpike ? 'high-dip' : 'high-spike';
    const threshold=Number(quality.min_effort_spread_points ?? 10);
    const perVariant=allTrialIds.map((trial)=>{
      const m=allTrialMaps.medium.get(trial);
      const h=allTrialMaps.high.get(trial);
      const x=allTrialMaps.xhigh.get(trial);
      if(!m||!h||!x) return {trial,magnitude_points:0,signal:false};
      const ms=Number(m.score??0), hs=Number(h.score??0), xs=Number(x.score??0);
      const value=direction==='high-dip'
        ? Math.min(ms,xs)-hs
        : hs-Math.max(ms,xs);
      return {trial,magnitude_points:value,signal:value>=threshold};
    });
    const signalCount=perVariant.filter(x=>x.signal).length;
    const variantConsistencyOk=trialMode!=='variants' ||
      repeatedVariantAgreement(['medium','high','xhigh'],distinctVariants,threshold,direction);
    nonMonotonic = {
      direction,
      magnitude_points:magnitude,
      signal_variant_count:signalCount,
      required_signal_variant_count:trialMode==='variants'?familyMinPositiveVariants:null,
      per_variant:trialMode==='variants'?perVariant:undefined,
      classification:repeated && stable && variantConsistencyOk
        ? 'nonmonotonic-effort-anomaly-confirmed'
        : 'nonmonotonic-effort-anomaly-candidate',
      repeated,
      stable,
    };
  }
}

let promotionRecommendation='do-not-promote';
if (comparison?.classification === 'quality-effort-confirmed') {
  promotionRecommendation='effort-discriminator-confirmed';
} else if (effortSensitivity?.classification === 'effort-sensitivity-confirmed') {
  promotionRecommendation='effort-sensitivity-confirmed';
}

const output = {
  generated_at: new Date().toISOString(),
  task: rows[0]?.task ?? null,
  model: rows[0]?.model ?? null,
  trial_count: Math.max(...Object.values(byEffort).map(x=>x.trials),0),
  trial_mode: trialMode,
  by_effort: byEffort,
  effort_spread_points: effortSpread,
  medium_to_xhigh: comparison,
  effort_sensitivity: effortSensitivity,
  nonmonotonic: nonMonotonic,
  promotion_recommendation: promotionRecommendation,
  promotion_evidence: {
    trial_mode: trialMode,
    paired_variants: commonTrials.length,
    repeat_rounds_required_per_variant: trialMode==='variants'?familyMinRepeatRounds:null,
    repeated_variant_evidence_complete: trialMode==='variants'
      ? hasPairedRepeatEvidence(effortStats.map(x=>x.effort),distinctVariants) : null,
    medium_to_xhigh_gain_points: comparison?.medium_to_xhigh_quality_gain_points ?? null,
    positive_variant_count: comparison?.positive_quality_trial_count ?? null,
    required_positive_variant_count: comparison?.required_positive_trial_count ?? null,
    effort_spread_points: effortSensitivity?.spread_points ?? effortSpread,
    budget_confounded: Boolean(
      comparison?.classification === 'budget-confounded' ||
      effortStats.some((x)=>x.saturated)
    ),
  },
};
fs.writeFileSync(outJson, JSON.stringify(output, null, 2) + '\n');

const f1 = (v) => v == null ? '-' : Number(v).toFixed(1);
const lines = [
  '# Frontier Effort Analysis',
  '',
  `Trial mode: ${trialMode}`,
  '',
  '| Effort | Trials | Quality mean | Quality stddev | Runtime avg | Shell avg | Probes avg | Patch files | Patch lines | Total tokens avg | Reasoning avg | Saturated |',
  '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|',
];
for (const key of ['medium','high','xhigh']) {
  const r = byEffort[key];
  if (!r) continue;
  lines.push(`| ${key} | ${r.trials} | ${f1(r.score)} | ${f1(r.score_stddev)} | ${Math.round(r.duration_seconds??0)}s | ${f1(r.shell_commands)} | ${f1(r.probe_calls)} | ${f1(r.changed_files)} | ${f1(r.changed_lines)} | ${Math.round(r.total_tokens??0)} | ${Math.round(r.reasoning_tokens??0)} | ${r.saturated ? 'yes' : 'no'} |`);
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
  `**Promotion recommendation:** \`${promotionRecommendation}\`.`,
  '',
  '> Directional quality improvement, generic effort sensitivity, efficiency, and non-monotonic anomalies are separate signals. Effort sensitivity means the chosen effort level reliably changes quality; it does not imply that higher effort is better. Formal effort-discriminator promotion still requires repeated positive Medium→X High quality gain.',
);
fs.writeFileSync(outMd, lines.join('\n') + '\n');
console.log(lines.join('\n'));
