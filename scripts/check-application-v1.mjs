import fs from 'node:fs';
import path from 'node:path';

const input = process.argv[2] ?? 'results/application-final-summary.json';
const outJson = process.argv[3] ?? 'results/application-v1-readiness.json';
const outMd = process.argv[4] ?? 'results/application-v1-readiness.md';
const report = JSON.parse(fs.readFileSync(input,'utf8'));
const registry = JSON.parse(fs.readFileSync('benchmarks/frontier-registry.json','utf8'));
const manifest = JSON.parse(fs.readFileSync('benchmarks/application-final-suite.json','utf8'));
const tasks = manifest.families.filter(t=>t.role==='core').map(t=>t.id);
const models = ['gpt-6-astra','gpt-6.1-sol','gpt-6-luna','gpt-5.6-sol'];
const expected = models.flatMap(model=>tasks.map(task=>({model,effort:'high',task})));
const rows = Array.isArray(report.rows) ? report.rows : [];
const hardLimit = Number(manifest.hard_timeout_seconds ?? 600);
const admissible = row => Boolean(row && row.data_complete === true &&
  row.runner_telemetry_present === true &&
  row.outcome === 'completed' && !row.infrastructure_error &&
  !row.model_timeout && !row.turn_limit_reached &&
  !row.shell_budget_reached && !row.probe_budget_reached &&
  Number.isFinite(Number(row.score)) &&
  Number(row.duration_seconds) <= hardLimit);
const checks = expected.map(({model,effort,task})=>{
  const row = rows.find(r=>r.model===model && r.effort===effort && r.task===task);
  return {model,effort,task,admissible:admissible(row),
    score:admissible(row)?Number(row.score):null,
    duration_seconds:row?.duration_seconds??null,
    reason:!row?'missing':admissible(row)?'completed':'incomplete-or-budget-confounded'};
});
const coreConfirmed = tasks.length>=2 && tasks.every(id=>registry.tasks.some(t=>
  t.id===id && t.promoted_to_final === true &&
  ['model-discriminator-confirmed','model+effort-discriminator-confirmed'].includes(t.status)));
const completeModels=models.filter(model=>tasks.every(task=>
  checks.some(c=>c.model===model && c.task===task && c.admissible)));
const fullMatrixComplete=completeModels.length===models.length;
const ready=coreConfirmed && completeModels.includes('gpt-6.1-sol') && completeModels.length>=2;
const status = {
  version:'0.1.0-beta.1', profile:'v1-core',
  generated_at:new Date().toISOString(),
  ready,
  application_suite_mature:false,
  effort_core_confirmed:false,
  full_model_epoch_validation:'pending',
  comparison_evidence:'single-run-directional-only; not a repeated ranking',
  core_confirmed_by_registry:coreConfirmed,
  full_matrix_complete:fullMatrixComplete,
  fully_valid_models:completeModels,
  required_results:checks.length,
  admissible_results:checks.filter(x=>x.admissible).length,
  core_families:tasks,
  models,checks,
};
fs.mkdirSync(path.dirname(outJson),{recursive:true});
fs.writeFileSync(outJson,JSON.stringify(status,null,2)+'\n');
const lines=[
  '# 应用评测 V1 Core（试用版）','',
  `**状态：${ready?'可用（试用版）':'未通过 V1 验收'}**。这是 2 道核心应用题 × 4 模型 / High 的一次性对照，不是完整五场景终验。`,
  '', '| 模型 | 题目 | 得分 | 耗时 | 样本 |',
  '|---|---|---:|---:|---|',
  ...checks.map(x=>`| ${x.model} | ${x.task} | ${x.score??'-'} | ${x.duration_seconds??'-'}s | ${x.admissible?'有效':'无效/缺失'} |`),
  '',
  `Model Core 注册表确认：${coreConfirmed?'已满足':'未满足'}；可比模型：${completeModels.join('、')||'无'}；有效样本：${status.admissible_results}/${status.required_results}。`,
  '',
  '> V1 最低可用门槛是 GPT-6.1 Sol 与至少一个其他模型均完成两道 Core 题；缺失配置不参与比较，四模型完整状态单独显示。单轮样本不应作为稳定排名、Effort 档位结论或降智判断。',
  '> Effort Core 未确认、完整当前模型纪元终验尚未完成；正式 maturity 判定不因 V1 可用而改变。',''
];
fs.writeFileSync(outMd,lines.join('\n'));
console.log(lines.join('\n'));
