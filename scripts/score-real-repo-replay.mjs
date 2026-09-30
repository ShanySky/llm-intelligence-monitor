import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const caseId=process.argv[2];
const root=path.resolve(process.argv[3]);
const resultPath=path.resolve(process.argv[4]);
const configPath=path.resolve(process.argv[5]);

const config=JSON.parse(fs.readFileSync(configPath,'utf8'));
const spec=config.cases.find(x=>x.id===caseId);
if(!spec) throw new Error('unknown replay case '+caseId);

const checks={};
let behavior=0;
function add(name,points,ok){
  checks[name]={points,passed:Boolean(ok)};
  if(ok) behavior+=points;
}
function writeJson(p,x){
  fs.mkdirSync(path.dirname(p),{recursive:true});
  fs.writeFileSync(p,JSON.stringify(x,null,2)+'\n');
}
function runNode(script,args,cwd=root){
  return spawnSync('node',[script,...args],{cwd,encoding:'utf8',timeout:30000,maxBuffer:1024*1024});
}
function readJson(p){
  try{return JSON.parse(fs.readFileSync(p,'utf8'));}catch{return null;}
}

const hiddenDir=path.join(root,'.replay-hidden');
fs.rmSync(hiddenDir,{recursive:true,force:true});
fs.mkdirSync(hiddenDir,{recursive:true});

const registryPath=path.join(root,'benchmarks/frontier-registry.json');
const hadRegistry=fs.existsSync(registryPath);
const registryBackup=hadRegistry?fs.readFileSync(registryPath):null;

function setRegistry(tasks){
  fs.mkdirSync(path.dirname(registryPath),{recursive:true});
  writeJson(registryPath,{version:1,tasks});
}
function restoreRegistry(){
  if(hadRegistry) fs.writeFileSync(registryPath,registryBackup);
  else fs.rmSync(registryPath,{force:true});
}

try{
  if(caseId==='repeat-evidence-promotion'){
    const analyzer=path.join(root,'scripts/analyze-application-discrimination.mjs');
    const policy={
      quality:{ceiling_score:95,min_model_spread_points:10,min_effort_directional_gain_points:10,min_trials_for_effort_confirmation:2,max_repeat_stddev_points:12},
      runtime:{hard_limit_seconds:600},
      selection:{},
      efficiency:{min_quality_floor:95,min_improvement_percent:15,min_improved_metrics:2}
    };
    const manifest={families:[{id:'taskA',family:'code_review',weight:100,role:'core'}],core_min_families_for_mature_score:1};
    const oneShot=[
      {task:'taskA',model:'gpt-5.6-sol',effort:'xhigh',score:80,data_complete:true,duration_seconds:10,usage:{}},
      {task:'taskA',model:'gpt-6-sol',effort:'xhigh',score:100,data_complete:true,duration_seconds:10,usage:{}}
    ];
    const repeated=[...oneShot,...oneShot.map(x=>({...x,duration_seconds:11}))];
    const policyPath=path.join(hiddenDir,'policy.json');
    writeJson(policyPath,policy);

    function evaluate(label,rows,registry){
      setRegistry(registry);
      const input=path.join(hiddenDir,label+'-input.json');
      const out=path.join(hiddenDir,label+'-out.json');
      const md=path.join(hiddenDir,label+'-out.md');
      writeJson(input,{manifest,rows});
      const p=runNode(analyzer,[input,policyPath,out,md]);
      return {proc:p,data:readJson(out)};
    }

    const one=evaluate('one-shot',oneShot,[]);
    const registry=evaluate('registry',oneShot,[{id:'taskA',status:'model-discriminator-confirmed',promoted_to_final:true}]);
    const repeat=evaluate('repeated',repeated,[]);

    add('analyzer_runs',10,one.proc.status===0&&registry.proc.status===0&&repeat.proc.status===0);
    add('one_shot_not_formally_confirmed',30,one.data?.tasks?.[0]?.model_signal_confirmed===false);
    add('registry_confirmation_preserved',30,registry.data?.tasks?.[0]?.model_signal_confirmed===true);
    add('repeated_current_evidence_can_confirm',20,repeat.data?.tasks?.[0]?.model_signal_confirmed===true);
    add('confirmation_source_exposed',10,
      typeof registry.data?.tasks?.[0]?.model_signal_source==='string' &&
      typeof one.data?.tasks?.[0]?.effort_signal_source==='string');
  }

  else if(caseId==='variant-effort-counts'){
    const analyzer=path.join(root,'scripts/analyze-effort-efficiency.mjs');
    const policy={
      quality:{
        min_effort_directional_gain_points:10,
        min_effort_spread_points:10,
        min_trials_for_effort_confirmation:3,
        max_repeat_stddev_points:12,
        min_directional_consistency_rate:0.67,
        effort_family_min_variants:3,
        effort_family_min_positive_variants:2,
        effort_family_variant_gain_points:10
      },
      efficiency:{min_quality_floor:95,min_improvement_percent:15,min_improved_metrics:2}
    };
    const policyPath=path.join(hiddenDir,'policy.json');
    writeJson(policyPath,policy);
    const rows=[];
    const medium=[60,60,100], xhigh=[80,80,90];
    for(let i=0;i<3;i++){
      rows.push({task:'family',model:'gpt-6-sol',effort:'medium',trial:i+1,score:medium[i],data_complete:true,duration_seconds:10,shell_commands:2,usage:{input_tokens:100,output_tokens:20}});
      rows.push({task:'family',model:'gpt-6-sol',effort:'xhigh',trial:i+1,score:xhigh[i],data_complete:true,duration_seconds:10,shell_commands:2,usage:{input_tokens:100,output_tokens:20}});
    }
    function evaluate(mode){
      const input=path.join(hiddenDir,mode+'-input.json');
      const out=path.join(hiddenDir,mode+'-out.json');
      const md=path.join(hiddenDir,mode+'-out.md');
      writeJson(input,{trial_mode:mode,rows});
      const p=runNode(analyzer,[input,policyPath,out,md]);
      return {proc:p,data:readJson(out)};
    }
    const variants=evaluate('variants');
    const repeats=evaluate('repeats');

    add('analyzer_runs',10,variants.proc.status===0&&repeats.proc.status===0);
    add('two_of_three_variants_confirm',50,variants.data?.medium_to_xhigh?.classification==='quality-effort-confirmed');
    add('explicit_positive_variant_count',20,
      variants.data?.medium_to_xhigh?.positive_quality_trial_count===2 &&
      variants.data?.medium_to_xhigh?.required_positive_trial_count===2);
    add('repeat_mode_keeps_rate_semantics',20,repeats.data?.medium_to_xhigh?.classification!=='quality-effort-confirmed');
  }

  else if(caseId==='split-core-maturity'){
    const analyzer=path.join(root,'scripts/analyze-application-discrimination.mjs');
    const policy={
      quality:{ceiling_score:95,min_model_spread_points:10,min_effort_directional_gain_points:10,min_trials_for_effort_confirmation:2,max_repeat_stddev_points:12},
      runtime:{hard_limit_seconds:600},
      selection:{model_core_min_families:2,effort_core_min_families:1},
      efficiency:{min_quality_floor:95,min_improvement_percent:15,min_improved_metrics:2}
    };
    const manifest={
      families:[
        {id:'coreA',family:'code_review',weight:50,role:'core'},
        {id:'coreB',family:'agent',weight:50,role:'core'}
      ],
      core_min_families_for_mature_score:2
    };
    const rows=[
      {task:'coreA',model:'gpt-6-sol',effort:'xhigh',score:90,data_complete:true,duration_seconds:10,usage:{}},
      {task:'coreB',model:'gpt-6-sol',effort:'xhigh',score:90,data_complete:true,duration_seconds:10,usage:{}}
    ];
    setRegistry([
      {id:'coreA',status:'model-discriminator-confirmed',promoted_to_final:true},
      {id:'coreB',status:'model-discriminator-confirmed',promoted_to_final:true},
      {id:'effortFamily',status:'effort-discriminator-confirmed',promoted_to_final:false}
    ]);
    const input=path.join(hiddenDir,'input.json'), policyPath=path.join(hiddenDir,'policy.json');
    const out=path.join(hiddenDir,'out.json'), md=path.join(hiddenDir,'out.md');
    writeJson(input,{manifest,rows}); writeJson(policyPath,policy);
    const p=runNode(analyzer,[input,policyPath,out,md]);
    const data=readJson(out);

    add('analyzer_runs',10,p.status===0);
    add('model_core_split',35,
      data?.core_signal?.model_core?.confirmed_families===2 &&
      data?.core_signal?.model_core?.mature===true);
    add('effort_core_split',35,
      data?.core_signal?.effort_core?.confirmed_families===1 &&
      data?.core_signal?.effort_core?.mature===true);
    add('overall_requires_both',20,data?.core_signal?.mature===true);
  }
} finally {
  restoreRegistry();
  fs.rmSync(hiddenDir,{recursive:true,force:true});
}

const runner=readJson(path.join(root,'light-agent-result.json'))??{};
const patch=runner.patch_metrics??{};
const allowed=new Set(spec.allowed_paths??[]);
const paths=Array.isArray(patch.files)?patch.files.map(x=>String(x.path??'')):[];
const unexpected=paths.filter(p=>p!=='TASK.md'&&!allowed.has(p));
const taskChanged=paths.includes('TASK.md');
let patchQuality=100;
if(taskChanged) patchQuality-=40;
patchQuality-=Math.min(40,unexpected.length*20);
const maxLines=Number(spec.preferred_max_changed_lines??100);
const changedLines=Number(patch.changed_lines??0);
if(changedLines>maxLines) patchQuality-=Math.min(30,((changedLines-maxLines)/maxLines)*30);
patchQuality=Math.max(0,Math.round(patchQuality*10)/10);

const behaviorScore=Math.max(0,Math.min(100,behavior));
const gate=behaviorScore>=80;
const replayScore=gate
  ? Math.round((behaviorScore*0.8+patchQuality*0.2)*10)/10
  : behaviorScore;

const output={
  task:'real-repo-replay-family',
  case_id:caseId,
  behavior_score:behaviorScore,
  patch_quality_score:gate?patchQuality:null,
  score:replayScore,
  behavior_gate_passed:gate,
  checks,
  patch_metrics:patch,
  unexpected_changed:unexpected,
  task_changed:taskChanged
};
fs.writeFileSync(resultPath,JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify(output,null,2));
