import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root=process.cwd();
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'effort-gate-'));
const scorer=path.join(root,'scripts/analyze-effort-efficiency.mjs');
const policy=path.join(root,'benchmarks/application-selection-policy.json');
const row=(trial,effort,repeat,score,extra={})=>({
  task:'real-repo-replay-family',model:'gpt-6.1-sol',trial,effort,
  ...(repeat===null?{}:{repeat}),score,
  outcome:'completed',data_complete:true,duration_seconds:150,shell_commands:5,
  usage:{input_tokens:2000,output_tokens:100},...extra
});
function score(key,rows){
  const input=path.join(dir,key+'-in.json'),output=path.join(dir,key+'-out.json');
  fs.writeFileSync(input,JSON.stringify({trial_mode:'variants',rows}));
  const p=spawnSync(process.execPath,[scorer,input,policy,output,path.join(dir,key+'.md')],{
    cwd:root,encoding:'utf8',timeout:15000});
  assert.equal(p.status,0,p.stderr||p.stdout);
  return JSON.parse(fs.readFileSync(output,'utf8'));
}
try{
  const single=[],stable=[],unstable=[],timed=[];
  for(let t=1;t<=3;t++){
    for(const [e,s] of [['medium',60],['high',72],['xhigh',85]])
      single.push(row(t,e,null,s));
    for(let r=1;r<=2;r++){
      stable.push(row(t,'medium',r,60),row(t,'high',r,72),row(t,'xhigh',r,85));
      unstable.push(row(t,'medium',r,r===1?60:90),
        row(t,'high',r,72),row(t,'xhigh',r,r===1?90:60));
      timed.push(row(t,'medium',r,60),row(t,'high',r,72),
        row(t,'xhigh',r,85,t===2&&r===2?{model_timeout:true,outcome:'model_timeout'}:{}));
    }
  }
  const a=score('single',single),b=score('stable',stable),
        c=score('unstable',unstable),d=score('timed',timed);
  assert.equal(a.promotion_recommendation,'do-not-promote');
  assert.equal(a.promotion_evidence.repeated_variant_evidence_complete,false);
  assert.equal(b.promotion_recommendation,'effort-discriminator-confirmed');
  assert.equal(b.promotion_evidence.repeated_variant_evidence_complete,true);
  assert.equal(c.promotion_recommendation,'do-not-promote');
  assert.equal(d.medium_to_xhigh.classification,'budget-confounded');
  assert.equal(d.promotion_recommendation,'do-not-promote');
  const mixed=stable.map(r=>({...r}));
  mixed[0].model='gpt-6-sol';
  const pathMixed=path.join(dir,'mixed.json');
  fs.writeFileSync(pathMixed,JSON.stringify({trial_mode:'variants',rows:mixed}));
  const mixedRun=spawnSync(process.execPath,[scorer,pathMixed,policy,
    path.join(dir,'mixed-out.json'),path.join(dir,'mixed.md')],{
    cwd:root,encoding:'utf8',timeout:15000});
  assert.notEqual(mixedRun.status,0,'mixed model epochs must be rejected');
  assert.match(mixedRun.stderr,/Mixed model epochs/);
  const opposing=[];
  const directions=[
    {medium:20,high:90,xhigh:70},
    {medium:50,high:90,xhigh:20},
    {medium:50,high:50,xhigh:50}
  ];
  for(let trial=1;trial<=3;trial++) for(let repeat=1;repeat<=2;repeat++)
    for(const effort of ['medium','high','xhigh'])
      opposing.push(row(trial,effort,repeat,directions[trial-1][effort]));
  assert.equal(score('opposing',opposing).promotion_recommendation,'do-not-promote');
  console.log('PASS: six replay evidence regression scenarios');
}finally{fs.rmSync(dir,{recursive:true,force:true});}
