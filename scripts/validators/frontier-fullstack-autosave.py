#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]

hidden=r'''
const { saveOrder } = require("./frontend/orderEditor");
const { AuditSink } = require("./backend/auditSink");
const { OrderService } = require("./backend/orderService");
const { ApiError } = require("./backend/errors");

function check(x, m) { if (!x) throw new Error(m || "check"); }

async function timeoutRetry() {
  const audit = new AuditSink();
  let once = true;
  const service = new OrderService(audit, {
    afterCommit() {
      if (once) {
        once = false;
        throw new ApiError("TIMEOUT", "response lost after commit");
      }
    }
  });
  service.seed("t", "draft", 1);
  const api={patch: async r=>service.patch(r), get: async id=>service.get(id)};
  const state={id:"t", value:"draft", version:1};
  const out=await saveOrder(api,state,{value:"ready"});
  check(out.version===2 && out.value==="ready","timeout result");
  check(service.get("t").version===2,"timeout duplicated version");
  check(audit.count()===1,"timeout duplicated audit");
  check(state.version===2 && state.value==="ready","timeout state");
}

async function conflictNoOverwrite() {
  const audit = new AuditSink();
  const service = new OrderService(audit);
  service.seed("c","base",1);
  service.patch({id:"c",expectedVersion:1,operationId:"remote-op",value:"remote"});
  const api={patch: async r=>service.patch(r), get: async id=>service.get(id)};
  const state={id:"c",value:"local-draft",version:1};
  let conflict=false;
  try { await saveOrder(api,state,{value:"local"}); }
  catch(e) { conflict=e && e.code==="CONFLICT"; }
  check(conflict,"conflict not surfaced");
  const row=service.get("c");
  check(row.version===2 && row.value==="remote","remote edit overwritten");
  console.log("STATE_" + (state.version===1 && state.value==="local-draft" ? "PASS" : "FAIL"));
}

async function backendRetrySameOperation() {
  const audit = new AuditSink();
  let once=true;
  const service=new OrderService(audit,{
    afterCommit(){
      if(once){ once=false; throw new ApiError("TIMEOUT","after commit"); }
    }
  });
  service.seed("b","base",1);
  const req={id:"b",expectedVersion:1,operationId:"stable-op",value:"saved"};
  let timed=false;
  try { service.patch(req); } catch(e) { timed=e && e.code==="TIMEOUT"; }
  check(timed,"no timeout");
  const out=service.patch(req);
  check(out.order.version===2 && out.order.value==="saved","retry result");
  check(service.get("b").version===2,"backend reapplied");
  check(audit.count()===1,"backend duplicate audit");
}

async function separateEdits() {
  const audit=new AuditSink();
  const service=new OrderService(audit);
  service.seed("s","v1",1);
  const api={patch: async r=>service.patch(r), get: async id=>service.get(id)};
  const state={id:"s",value:"v1",version:1};
  await saveOrder(api,state,{value:"v2"});
  await saveOrder(api,state,{value:"v3"});
  check(service.get("s").version===3 && service.get("s").value==="v3","separate versions");
  check(audit.count()===2,"separate edits collapsed");
}

async function run(name, fn) {
  try { await fn(); console.log(name+"_PASS"); }
  catch(e) { console.log(name+"_FAIL:"+(e && e.message)); }
}

(async()=>{
  await run("TIMEOUT",timeoutRetry);
  await run("CONFLICT",conflictNoOverwrite);
  await run("BACKEND_RETRY",backendRetrySameOperation);
  await run("SEPARATE",separateEdits);
})().catch(e=>{ console.error(e); process.exit(2); });
'''

result={"syntax":False,"visible":False,"timeout":False,"conflict":False,"state":False,"backend_retry":False,"separate":False,"raw":""}

syntax=subprocess.run(
    ["node","--check","frontend/orderEditor.js"],
    cwd=root,capture_output=True,text=True
)
syntax2=subprocess.run(
    ["node","--check","backend/orderService.js"],
    cwd=root,capture_output=True,text=True
)
result["syntax"]=syntax.returncode==0 and syntax2.returncode==0

if result["syntax"]:
    vis=subprocess.run(["node","visible-test.js"],cwd=root,capture_output=True,text=True,timeout=20)
    result["visible"]=vis.returncode==0
    run=subprocess.run(["node","-e",hidden],cwd=root,capture_output=True,text=True,timeout=30)
    raw=(run.stdout or "")+(run.stderr or "")
    result["raw"]=raw
    result["timeout"]="TIMEOUT_PASS" in raw
    result["conflict"]="CONFLICT_PASS" in raw
    result["state"]="STATE_PASS" in raw
    result["backend_retry"]="BACKEND_RETRY_PASS" in raw
    result["separate"]="SEPARATE_PASS" in raw

if json_mode:
    print(json.dumps(result))
    raise SystemExit(0)

if not result["syntax"]:
    print("VALIDATION_FAIL syntax")
    raise SystemExit(1)
if not result["timeout"]:
    print("VALIDATION_FAIL timeout-retry: one logical edit does not converge after response loss")
    raise SystemExit(1)
if not result["conflict"] or not result["state"]:
    print("VALIDATION_FAIL conflict: stale editor converts 409 into overwrite or mutates local state")
    raise SystemExit(1)
if not result["backend_retry"]:
    print("VALIDATION_FAIL backend-recovery: same operation cannot recover after commit-before-response failure")
    raise SystemExit(1)
if not result["separate"]:
    print("VALIDATION_FAIL operation-scope: separate user edits no longer remain distinct")
    raise SystemExit(1)
print("VALIDATION_PASS: timeout recovery, conflict safety, local state, backend replay, and separate edit identity all pass")
