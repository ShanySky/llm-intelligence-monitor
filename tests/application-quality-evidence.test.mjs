import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const root=process.cwd();
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'app-quality-evidence-'));
const run=(script,...args)=>{
  const p=spawnSync(process.execPath,[path.join(root,script),...args],{
    cwd:root,encoding:'utf8',timeout:15000
  });
  assert.equal(p.status,0,p.stderr||p.stdout);
};
const write=(p,value)=>{
  fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(p,JSON.stringify(value,null,2)+'\n');
};
try{
  const manifest={
    core_min_families_for_mature_score:1,hard_timeout_seconds:600,
    families:[
      {id:'coreA',role:'core',family:'code_review',weight:50},
      {id:'coverageB',role:'coverage',family:'coding',weight:50}
    ],
    resident_model_epoch:{
      resident_sol_model:'gpt-6.1-sol',
      cross_model_set:['gpt-6.1-sol']
    }
  };
  const model='gpt-6.1-sol';
  const row=(task,score,outcome)=>({
    task,model,effort:'high',score,outcome,
    data_complete:true,
    model_timeout:outcome==='model_timeout',
    agent_exit_code:outcome==='completed'?0:124,
    duration_seconds:120,usage:{input_tokens:1000,output_tokens:200}
  });
  const manifestPath=path.join(tmp,'manifest.json');
  const input=path.join(tmp,'rows');
  const out=path.join(tmp,'summary.json');
  const md=path.join(tmp,'summary.md');
  write(manifestPath,manifest);
  write(path.join(input,'core','result.json'),row('coreA',85,'completed'));
  write(path.join(input,'timeout','result.json'),row('coverageB',100,'model_timeout'));
  run('scripts/summarize-application-results.mjs',input,manifestPath,out,md);
  const summary=JSON.parse(fs.readFileSync(out,'utf8'));
  const stat=summary.by_config[model+'|high'];
  assert.equal(stat.quality_score,85,'timeout patch score must not inflate quality');
  assert.equal(stat.core_quality_score,85);
  assert.equal(stat.data_complete,false,'quality comparison must be incomplete');
  assert.equal(stat.telemetry_complete,true,'telemetry remains available');
  assert.equal(stat.budget_completion_rate,0.5);
  assert.deepEqual(stat.incomplete_tasks,['coverageB']);
  assert.match(fs.readFileSync(md,'utf8'),/超时\/预算混淆/);

  const discPath=path.join(tmp,'disc.json');
  const discMd=path.join(tmp,'disc.md');
  run('scripts/analyze-application-discrimination.mjs',out,
    path.join(root,'benchmarks/application-selection-policy.json'),discPath,discMd);
  const disc=JSON.parse(fs.readFileSync(discPath,'utf8'));
  assert.equal(disc.tasks.find(t=>t.task==='coverageB').classification,
    'incomplete-or-budget-confounded');
  // Even if a trusted registry confirms signal families, an invalid current
  // suite cannot be declared mature.
  disc.core_signal.model_core.mature=true;
  disc.core_signal.effort_core.mature=true;
  write(discPath,disc);
  const maturePath=path.join(tmp,'mature.json');
  run('scripts/check-application-maturity.mjs',out,discPath,
    path.join(root,'benchmarks/frontier-registry.json'),manifestPath,
    maturePath,path.join(tmp,'mature.md'));
  const mature=JSON.parse(fs.readFileSync(maturePath,'utf8'));
  assert.equal(mature.checks.final_quality_evidence_complete,false);
  assert.equal(mature.checks.model_core,false);
  assert.equal(mature.automatic_mature,false);
  console.log('PASS: application quality excludes timeout and maturity blocks confounded data');
} finally {
  fs.rmSync(tmp,{recursive:true,force:true});
}
