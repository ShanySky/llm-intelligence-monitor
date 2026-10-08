import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const root=fs.mkdtempSync(path.join(os.tmpdir(),'application-v1-test-'));
try {
  const families=['frontier-review-deep','hard-incident'];
  const models=['gpt-6-astra','gpt-6.1-sol','gpt-6-luna','gpt-5.6-sol'];
  const rows=models.flatMap(model=>families.map(task=>({
    model,effort:'high',task,score:95,duration_seconds:30,
    data_complete:true,runner_telemetry_present:true,outcome:'completed',
    model_timeout:false,turn_limit_reached:false,shell_budget_reached:false,
    probe_budget_reached:false,infrastructure_error:null
  })));
  const input=path.join(root,'input.json'),json=path.join(root,'v1.json'),md=path.join(root,'v1.md');
  const check=()=> {
    fs.writeFileSync(input,JSON.stringify({rows}));
    execFileSync('node',['scripts/check-application-v1.mjs',input,json,md],{stdio:'pipe'});
    return JSON.parse(fs.readFileSync(json));
  };
  let valid=check();
  if(!valid.ready || !valid.full_matrix_complete || valid.admissible_results!==8)throw new Error('valid 4x2 matrix not accepted');
  rows[0].turn_limit_reached=true;
  let invalid=check();
  if(!invalid.ready || invalid.full_matrix_complete || invalid.admissible_results!==7)throw new Error('partial release or turn-limit rejection incorrect');
  rows[0].turn_limit_reached=false;rows[0].runner_telemetry_present=false;
  invalid=check();
  if(!invalid.ready || invalid.full_matrix_complete || invalid.admissible_results!==7)throw new Error('missing telemetry rejection incorrect');
  rows[0].runner_telemetry_present=true;rows[0].model='gpt-6-sol';
  invalid=check();
  if(!invalid.ready || invalid.full_matrix_complete || invalid.admissible_results!==7)throw new Error('legacy sol epoch not rejected');
  rows[0].model='gpt-6-astra';rows[0].runner_telemetry_present=true;
  const resident=rows.find(r=>r.model==='gpt-6.1-sol');
  resident.data_complete=false;
  invalid=check();
  if(invalid.ready)throw new Error('release accepted without resident Sol');
  console.log('PASS V1 full and partial readiness, budget, telemetry, old epoch, resident Sol requirement');
}finally{fs.rmSync(root,{recursive:true,force:true});}
