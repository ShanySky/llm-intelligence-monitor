import fs from 'node:fs';

const appPath=process.argv[2] ?? 'results/application-final-summary.json';
const discrPath=process.argv[3] ?? 'results/application-discrimination.json';
const registryPath=process.argv[4] ?? 'benchmarks/frontier-registry.json';
const manifestPath=process.argv[5] ?? 'benchmarks/application-final-suite.json';
const outJson=process.argv[6] ?? 'results/application-maturity.json';
const outMd=process.argv[7] ?? 'results/application-maturity.md';

const app=JSON.parse(fs.readFileSync(appPath,'utf8'));
const discr=JSON.parse(fs.readFileSync(discrPath,'utf8'));
const registry=JSON.parse(fs.readFileSync(registryPath,'utf8'));
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));

const rows=app.rows ?? [];
const policy=discr.policy ?? {};
const modelCore=discr.core_signal?.model_core ?? {};
const effortCore=discr.core_signal?.effort_core ?? {};

const requiredFamilies=[
  'solution_design',
  'coding',
  'code_review',
  'agent',
  'long_horizon',
];

function familyBucket(f){
  const x=String(f??'');
  if(x.includes('solution_design')) return 'solution_design';
  if(x.includes('code_review')) return 'code_review';
  if(x.includes('agent')) return 'agent';
  if(x.includes('long_horizon')) return 'long_horizon';
  if(x.includes('coding')) return 'coding';
  return null;
}
const covered=new Set(manifest.families.map(x=>familyBucket(x.family)).filter(Boolean));
const familyCoverage=Object.fromEntries(requiredFamilies.map(x=>[x,covered.has(x)]));

const hardLimit=Number(manifest.hard_timeout_seconds ?? 600);
const maxDuration=rows.length?Math.max(...rows.map(r=>Number(r.duration_seconds??0))):null;
const durationPass=maxDuration==null || maxDuration<=hardLimit;

const residentEpoch=manifest.resident_model_epoch ?? {};
const residentSolModel=residentEpoch.resident_sol_model ?? registry.resident_model_epoch?.resident_sol_model ?? null;
const expectedCrossModels=Array.isArray(residentEpoch.cross_model_set)?residentEpoch.cross_model_set:[];
const observedModels=new Set(rows.map((r)=>String(r.model??'')).filter(Boolean));
const configSummaries=Object.values(app.by_config??{});
const completeConfigs=configSummaries.filter(s=>s.data_complete===true && s.core_data_complete===true);
const completeModels=new Set(completeConfigs.map(s=>String(s.model??'')).filter(Boolean));
const currentQualityComplete=configSummaries.length>0 &&
  completeConfigs.length===configSummaries.length;
const crossModelEpochPass=expectedCrossModels.length===0 ||
  expectedCrossModels.every((m)=>completeModels.has(m));
const residentSolEfforts=new Set(
  completeConfigs
    .filter(s=>!residentSolModel || s.model===residentSolModel)
    .map(s=>String(s.effort??''))
    .filter(Boolean)
);
const residentEffortPass=!residentSolModel || ['medium','high','xhigh'].every((e)=>residentSolEfforts.has(e));
const finalModelEpochPass=crossModelEpochPass && residentEffortPass;

const quickWorkflow='.github/workflows/intelligence-smoke.yml';
const quickText=fs.existsSync(quickWorkflow)?fs.readFileSync(quickWorkflow,'utf8'):'';
const quickHealthPass=
  quickText.includes('analyze-question-health.mjs') &&
  quickText.includes('QUESTION_HEALTH_PATH');

const finalWorkflowPass=fs.existsSync('.github/workflows/application-final-validation.yml');
const refreshWorkflowPass=fs.existsSync('.github/workflows/application-report-refresh.yml');
const readme=fs.existsSync('README.md')?fs.readFileSync('README.md','utf8'):'';
const docsPass=
  readme.includes('Model Core') &&
  readme.includes('Effort Core') &&
  readme.includes('frontier-registry.json');

const modelCorePass=Boolean(modelCore.mature && currentQualityComplete);
const effortCorePass=Boolean(effortCore.mature);
const coveragePass=Object.values(familyCoverage).every(Boolean);

const confirmedModelTasks=(registry.tasks??[]).filter(x=>
  x.promoted_to_final &&
  ['model-discriminator-confirmed','model+effort-discriminator-confirmed'].includes(x.status)
).map(x=>x.id);
const confirmedEffortTasks=(registry.tasks??[]).filter(x=>
  ['effort-discriminator-confirmed','model+effort-discriminator-confirmed','effort-sensitivity-confirmed'].includes(x.status) &&
  (!residentSolModel || x?.evidence?.resident_sol_model===residentSolModel)
).map(x=>x.id);

const checks={
  model_core:modelCorePass,
  effort_core:effortCorePass,
  final_quality_evidence_complete:currentQualityComplete,
  application_family_coverage:coveragePass,
  duration_hard_limit:durationPass,
  final_model_epoch_coverage:finalModelEpochPass,
  quick_monitor_health_integration:quickHealthPass,
  final_application_workflow:finalWorkflowPass,
  report_refresh_workflow:refreshWorkflowPass,
  docs_and_registry:docsPass,
};

const automaticMature=Object.values(checks).every(Boolean);
const output={
  generated_at:new Date().toISOString(),
  automatic_mature:automaticMature,
  checks,
  model_core:{
    ...modelCore,
    registry_confirmed_tasks:confirmedModelTasks,
  },
  effort_core:{
    ...effortCore,
    resident_sol_model:residentSolModel,
    registry_confirmed_tasks:confirmedEffortTasks,
  },
  application_family_coverage:familyCoverage,
  runtime:{
    hard_limit_seconds:hardLimit,
    max_observed_task_seconds:maxDuration,
  },
  final_model_epoch:{
    resident_sol_model:residentSolModel,
    expected_cross_models:expectedCrossModels,
    observed_models:[...observedModels].sort(),
    quality_complete_models:[...completeModels].sort(),
    cross_model_coverage:crossModelEpochPass,
    resident_sol_efforts:[...residentSolEfforts].sort(),
    resident_sol_effort_coverage:residentEffortPass,
    mature:finalModelEpochPass,
  },
  manual_acceptance_remaining:[
    'Confirm application scores remain consistent with real day-to-day Coding/Agent experience over continued use.',
    'Confirm the on-demand quick-monitor cost remains acceptable across representative normal runs.'
  ],
};
fs.mkdirSync('results',{recursive:true});
fs.writeFileSync(outJson,JSON.stringify(output,null,2)+'\n');

const yn=x=>x?'PASS':'WAIT';
const lines=[
  '# Application Benchmark Maturity','',
  '| Check | Status |',
  '|---|---|',
  `| Model Core | ${yn(checks.model_core)} |`,
  `| Effort Core | ${yn(checks.effort_core)} |`,
  `| Final quality evidence complete | ${yn(checks.final_quality_evidence_complete)} |`,
  `| Five application families | ${yn(checks.application_family_coverage)} |`,
  `| Per-task hard runtime limit | ${yn(checks.duration_hard_limit)} |`,
  `| Current model-epoch final validation | ${yn(checks.final_model_epoch_coverage)} |`,
  `| Quick monitor health integration | ${yn(checks.quick_monitor_health_integration)} |`,
  `| Final application workflow | ${yn(checks.final_application_workflow)} |`,
  `| Cost-free report refresh | ${yn(checks.report_refresh_workflow)} |`,
  `| README / registry integration | ${yn(checks.docs_and_registry)} |`,
  '',
  `**Automatic maturity:** ${automaticMature?'PASS':'NOT YET'}`,
  '',
  `Model Core: ${modelCore.confirmed_families??0}/${modelCore.minimum_families??'-'}; Effort Core: ${effortCore.confirmed_families??0}/${effortCore.minimum_families??'-'}.`,
  `Max observed task runtime: ${maxDuration??'-'}s / hard limit ${hardLimit}s.`,
  `Current model epoch: resident=${residentSolModel??'-'}; cross-model coverage=${crossModelEpochPass?'complete':'incomplete'}; resident M/H/XH=${residentEffortPass?'complete':'incomplete'}.`,
  '',
  '> Two acceptance items remain intentionally manual: real-use alignment and representative on-demand operating cost. They should not be faked by a static repository check.',
  ''
];
fs.writeFileSync(outMd,lines.join('\n'));
console.log(lines.join('\n'));
