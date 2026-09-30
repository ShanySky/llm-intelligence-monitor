import fs from 'node:fs';

const summaryPath=process.argv[2];
const manifestPath=process.argv[3];
const outJson=process.argv[4] ?? 'patch-quality-summary.json';
const outMd=process.argv[5] ?? 'patch-quality-summary.md';

const data=JSON.parse(fs.readFileSync(summaryPath,'utf8'));
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
const rows=Array.isArray(data.rows)?data.rows:[];

function scoreRow(result){
  const behavior=Number(result.score??0);
  const patch=result.patch_metrics??{};
  const files=Array.isArray(patch.files)?patch.files:[];
  const allowed=new Set(manifest.allowed_paths??[]);
  const forbidden=new Set(manifest.forbidden_paths??[]);
  const paths=files.map(x=>String(x.path??''));
  const forbiddenChanged=paths.filter(x=>forbidden.has(x));
  const unexpected=paths.filter(x=>!allowed.has(x)&&!forbidden.has(x));
  const gate=behavior>=Number(manifest.behavior_gate_score??95);
  if(!gate) return {...result,patch_quality_score:null,patch_quality_gate:false,forbidden_changed:forbiddenChanged,unexpected_changed:unexpected};

  const weights=manifest.scoring??{};
  const integrity=forbiddenChanged.length===0?Number(weights.forbidden_integrity??40):0;
  const scopeWeight=Number(weights.allowed_scope??30);
  const scope=unexpected.length===0?scopeWeight:Math.max(0,scopeWeight-10*unexpected.length);

  const footprintWeight=Number(weights.footprint??30);
  const maxFiles=Number(manifest.preferred_max_changed_files??6);
  const maxLines=Number(manifest.preferred_max_changed_lines??100);
  const maxAdded=Number(manifest.max_added_files??1);
  const fileRatio=maxFiles>0?Number(patch.changed_files??0)/maxFiles:1;
  const lineRatio=maxLines>0?Number(patch.changed_lines??0)/maxLines:1;
  const addedOver=Math.max(0,Number(patch.added_files??0)-maxAdded);
  let footprint=footprintWeight;
  if(fileRatio>1) footprint-=Math.min(10,(fileRatio-1)*20);
  if(lineRatio>1) footprint-=Math.min(15,(lineRatio-1)*15);
  footprint-=Math.min(10,addedOver*5);
  footprint=Math.max(0,footprint);

  return {
    ...result,
    patch_quality_gate:true,
    patch_quality_score:Math.round((integrity+scope+footprint)*10)/10,
    patch_quality_parts:{integrity,scope,footprint},
    forbidden_changed:forbiddenChanged,
    unexpected_changed:unexpected,
  };
}

const scored=rows.map(scoreRow);
const efforts=[...new Set(scored.map(x=>x.effort).filter(Boolean))];
const mean=xs=>xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:null;
const byEffort={};
for(const effort of efforts){
  const xs=scored.filter(x=>x.effort===effort);
  const qs=xs.map(x=>x.patch_quality_score).filter(Number.isFinite);
  byEffort[effort]={
    trials:xs.length,
    behavior_mean:mean(xs.map(x=>Number(x.score??0))),
    patch_quality_mean:mean(qs),
    patch_quality_trials:qs.length,
    changed_files_mean:mean(xs.map(x=>Number(x.patch_metrics?.changed_files??0))),
    changed_lines_mean:mean(xs.map(x=>Number(x.patch_metrics?.changed_lines??0))),
    unexpected_files_mean:mean(xs.map(x=>Number(x.unexpected_changed?.length??0))),
    integrity_failures:xs.filter(x=>(x.forbidden_changed??[]).length>0).length,
  };
}
const pq=Object.values(byEffort).map(x=>x.patch_quality_mean).filter(Number.isFinite);
const output={
  generated_at:new Date().toISOString(),
  task:rows[0]?.task??null,
  manifest,
  rows:scored,
  by_effort:byEffort,
  patch_quality_spread_points:pq.length?Math.max(...pq)-Math.min(...pq):null,
};
fs.writeFileSync(outJson,JSON.stringify(output,null,2)+'\n');

const f1=v=>v==null?'-':Number(v).toFixed(1);
const lines=[
  '# Patch Quality Analysis','',
  '| Effort | Trials | Behavior | Patch quality | Changed files | Changed lines | Unexpected files | Integrity failures |',
  '|---|---:|---:|---:|---:|---:|---:|---:|',
];
for(const effort of ['medium','high','xhigh']){
  const x=byEffort[effort]; if(!x) continue;
  lines.push(`| ${effort} | ${x.trials} | ${f1(x.behavior_mean)} | ${f1(x.patch_quality_mean)} | ${f1(x.changed_files_mean)} | ${f1(x.changed_lines_mean)} | ${f1(x.unexpected_files_mean)} | ${x.integrity_failures} |`);
}
lines.push('',`Patch-quality spread: ${f1(output.patch_quality_spread_points)} points.`,'');
fs.writeFileSync(outMd,lines.join('\n'));
console.log(lines.join('\n'));
