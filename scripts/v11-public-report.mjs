import fs from 'node:fs';
import path from 'node:path';

// Public V1.1 evidence report: synthesize immutable real-run evidence.
// Not a model ranking and never fill a missing / budget-exhausted score with zero.
export function buildReport(input) {
  const corrected = input.corrected_luna;
  const easy = input.luna_easy;
  const mid = input.luna_mid;
  const sol = input.sol;
  const rows = [];
  const put = (task, model, effort, score, valid, duration, source, sourceRun, note='', usage=null) => {
    const complete = valid === true && (score === 0 || Number.isFinite(score));
    rows.push({task,model,effort,score:complete?Number(score):null,
      data_complete:complete,duration_seconds:Number.isFinite(Number(duration))?Number(duration):null,
      source,source_run_id:sourceRun??null,explanation:note,
      input_tokens:Number.isFinite(Number(usage?.input_tokens))?Number(usage.input_tokens):null,
      output_tokens:Number.isFinite(Number(usage?.output_tokens))?Number(usage.output_tokens):null,
      reasoning_tokens:Number.isFinite(Number(usage?.reasoning_tokens))?Number(usage.reasoning_tokens):null});
  };
  if (Array.isArray(corrected?.rows)) {
    for(const row of corrected.rows) {
      put(row.task,'gpt-6-luna','high',row.corrected_score,row.data_complete,
        row.agent_duration_seconds,'historical-original-patch-corrected-grader',
        row.original_model_run_id??corrected.original_luna_cohort_run_id,
        'Original agent had not yet received offline local-test preheat; not a like-for-like ongoing benchmark.');
    }
  }
  for(const [report,label] of [[easy,'historical-coverage-pilot'],[mid,'historical-exploratory-pilot']]) {
    if(!Array.isArray(report?.rows))continue;
    for(const row of report.rows)put(row.task,row.model??'gpt-6-luna',row.effort??'high',
      row.score,row.data_complete,row.duration_seconds,label,report.run_id,
      row.data_complete?'Single-pass screening; not stability-confirmed.':'Invalid observation: budget, timeout, or infrastructure.',
      row.usage);
  }
  if(Array.isArray(sol?.rows))for(const row of sol.rows)put(
    row.task,row.model??'gpt-6.1-sol',row.effort??'high',row.score,row.data_complete,
    row.duration_seconds,'historical-sol-matched-vue',sol.run_id,
    'Only paired Vue tasks, one attempt each.',row.usage);
  rows.sort((a,b)=>a.task.localeCompare(b.task)||a.model.localeCompare(b.model)||a.effort.localeCompare(b.effort));
  const valid=rows.filter(x=>x.data_complete),invalid=rows.filter(x=>!x.data_complete);
  const mat=['vuejs__core-11589','vuejs__core-11899'];
  const pairs=mat.map(task=>({task,luna:rows.find(x=>x.task===task&&x.model==='gpt-6-luna'),
                                  sol:rows.find(x=>x.task===task&&x.model==='gpt-6.1-sol')}));
  const pairedValid=pairs.every(x=>x.luna?.data_complete&&x.sol?.data_complete);
  const qualityScore=(list)=>list.length&&list.every(x=>x.data_complete)
    ? Number((list.reduce((sum,r)=>sum+r.score,0)/list.length).toFixed(1)) : null;
  const lunaPaired=pairedValid?qualityScore(pairs.map(x=>x.luna)):null;
  const solPaired=pairedValid?qualityScore(pairs.map(x=>x.sol)):null;
  const easyRows=rows.filter(x=>x.source==='historical-coverage-pilot');
  const report={
    schema_version:1,release:'v1.1.0-beta',profile:'v1.1-evidence',
    type:'historical-verified-samples-not-live-score',
    public_original_task_evidence:true,requires_model_calls:false,
    generated_at:new Date().toISOString(),ready:rows.length>0,
    status:'usable-beta-evidence-report-effort-validation-pending',
    rows,counts:{total:rows.length,valid:valid.length,invalid:invalid.length},
    coverage:{tasks:easyRows.map(x=>x.task),quality_score:qualityScore(easyRows),
      evidence:'single-run-coverage-only-not-discriminator'},
    matched_pair:{
      tasks:mat,complete:pairedValid,luna_high:lunaPaired,sol_high:solPaired,
      spread_points:pairedValid?solPaired-lunaPaired:null,
      evidence:'single-attempt-candidate-only',
    },
    flags:{repeated_model_spread_confirmed:false,effort_spread_confirmed:false,
      astra_xhigh_calibrated:false,release_is_mature_benchmark:false},
    caveats:[
      'Historical runs from different rounds are not a same-condition model ranking.',
      'Two matched Vue cases give a provisional, unrepeated difference only.',
      'A budget-confounded or infrastructure-invalid case has score=null, not zero.',
      'Prior Gson/Axios source agent tests had missing dependencies; the corrected grader result is reported with provenance.',
      'No Medium/X High comparison has yet been established on a stable public-task cohort.'
    ]
  };
  return report;
}
const fmt=x=>x===null||x===undefined?'-':String(x);
export function renderMarkdown(report){
  const lines=[
    '# V1.1 公开工程评测：可用测试版证据报告','',
    '**报告类型：历史实测汇总（不调用模型）**。已接入原版 SWE-bench Java/Vue/JS 案例及官方测试；不能作为稳定模型排行榜。','',
    '| 原版任务 | 模型 / 档位 | 质量分 | 模型耗时 | 输入 Token | 数据状态 | 来源运行 |',
    '|---|---|---:|---:|---:|---|---|',
    ...report.rows.map(r=>`| ${r.task} | ${r.model} / ${r.effort} | ${fmt(r.score)} | ${fmt(r.duration_seconds)}s | ${fmt(r.input_tokens)} | ${r.data_complete?'有效':'无效 / 不计分'} | ${fmt(r.source_run_id)} |`),
    '','## 目前可以确认什么','',
    `- 公共工程历史样本：${report.counts.valid} 个有效、${report.counts.invalid} 个无效；无效数据不会被记为 0 分。`,
    `- 四道容易任务（Coverage）：${fmt(report.coverage.quality_score)} 分。该分数仅表示单轮覆盖，不用于证明模型差异。`,
    `- 同题 Vue 双样本初步对照：Luna High ${fmt(report.matched_pair.luna_high)}，Sol High ${fmt(report.matched_pair.sol_high)}，分差 ${fmt(report.matched_pair.spread_points)}；每题每模型只有一次，**未经稳定复验**。`,
    '- 思考档位 Medium/High/X High 能力区分 **待验证**，Astra 目标 **待验证**。','',
    '## 实际使用与下一步','',
    'V1 已有的手动 Core 模型评测入口保持可用。本 V1.1 报告仅汇总此前通过实际测试的公开工程题、Token、耗时及数据有效性；不自动触发任何付费运行。',
    '后续题目扩充、档位验证和 60/80/95 目标属于持续优化，不影响测试版的使用。','',
    '### 重要限制','',
    ...report.caveats.map(s=>'- '+s),''
  ];
  return lines.join('\n');
}
if(process.argv[1]&&path.resolve(process.argv[1])===path.resolve(new URL(import.meta.url).pathname)){
  const inputPath=process.argv[2],jsonPath=process.argv[3],mdPath=process.argv[4];
  if(!inputPath||!jsonPath||!mdPath)throw Error('Usage: node scripts/v11-public-report.mjs input.json output.json output.md');
  const report=buildReport(JSON.parse(fs.readFileSync(inputPath,'utf8')));
  for(const p of [jsonPath,mdPath])fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(jsonPath,JSON.stringify(report,null,2)+'\n');
  fs.writeFileSync(mdPath,renderMarkdown(report));
  console.log('V1.1 evidence rows:',report.counts.total,'valid:',report.counts.valid,
              'invalid:',report.counts.invalid,'paired:',report.matched_pair.complete);
}