import assert from 'node:assert/strict';
import {buildReport,renderMarkdown} from './v11-public-report.mjs';
const pack={
 corrected_luna:{original_luna_cohort_run_id:1,rows:[
  {task:'vuejs__core-11589',corrected_score:0,data_complete:true,agent_duration_seconds:161},
  {task:'vuejs__core-11899',corrected_score:0,data_complete:true,agent_duration_seconds:519},
  {task:'google__gson-2311',corrected_score:100,data_complete:true,agent_duration_seconds:128}
 ]},
 luna_easy:{run_id:2,rows:[{task:'google__gson-1093',model:'gpt-6-luna',effort:'high',score:100,data_complete:true,duration_seconds:100,usage:{input_tokens:45}}]},
 luna_mid:{run_id:3,rows:[{task:'vuejs__core-11739',model:'gpt-6-luna',effort:'high',score:null,data_complete:false,duration_seconds:230}]},
 sol:{run_id:4,rows:[
  {task:'vuejs__core-11589',model:'gpt-6.1-sol',effort:'high',score:100,data_complete:true,duration_seconds:199},
  {task:'vuejs__core-11899',model:'gpt-6.1-sol',effort:'high',score:0,data_complete:true,duration_seconds:240}
 ]}
};
const r=buildReport(pack);
assert.equal(r.counts.valid,6);assert.equal(r.counts.invalid,1);
assert.equal(r.matched_pair.complete,true);
assert.equal(r.matched_pair.spread_points,50);
assert.equal(r.rows.find(x=>x.task==='vuejs__core-11739').score,null);
assert.equal(r.flags.effort_spread_confirmed,false);
assert.match(renderMarkdown(r),/未经稳定复验/);
const partial=buildReport({...pack,sol:{rows:[]}});
assert.equal(partial.matched_pair.complete,false);
assert.equal(partial.matched_pair.spread_points,null);
const missing=buildReport({});
assert.equal(missing.ready,false);assert.equal(missing.counts.valid,0);
console.log('PASS V1.1 report real-evidence rows, invalid/null sample, matched-only, no false effort maturity, missing input');
