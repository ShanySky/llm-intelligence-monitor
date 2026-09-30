import fs from 'node:fs';

const resultPath=process.argv[2];
const manifestPath=process.argv[3];
const outPath=process.argv[4] ?? 'patch-quality.json';

const result=JSON.parse(fs.readFileSync(resultPath,'utf8'));
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
const behavior=Number(result.score??0);
const patch=result.patch_metrics??{};
const files=Array.isArray(patch.files)?patch.files:[];

const allowed=new Set(manifest.allowed_paths??[]);
const forbidden=new Set(manifest.forbidden_paths??[]);
const changedPaths=files.map(x=>String(x.path??''));
const forbiddenChanged=changedPaths.filter(x=>forbidden.has(x));
const unexpected=changedPaths.filter(x=>!allowed.has(x)&&!forbidden.has(x));

const gate=behavior>=Number(manifest.behavior_gate_score??95);
let score=null;
let parts={};
if(gate){
  const weights=manifest.scoring??{};
  const integrity=forbiddenChanged.length===0?Number(weights.forbidden_integrity??40):0;

  const scopeWeight=Number(weights.allowed_scope??30);
  const scope=unexpected.length===0
    ? scopeWeight
    : Math.max(0,scopeWeight-10*unexpected.length);

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

  parts={integrity,scope,footprint};
  score=Math.round((integrity+scope+footprint)*10)/10;
}

const output={
  task:result.task??null,
  model:result.model??null,
  effort:result.effort??null,
  trial:result.trial??null,
  behavior_score:behavior,
  behavior_gate_passed:gate,
  patch_quality_score:score,
  patch_metrics:patch,
  forbidden_changed:forbiddenChanged,
  unexpected_changed:unexpected,
  parts,
};
fs.writeFileSync(outPath,JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify(output,null,2));
