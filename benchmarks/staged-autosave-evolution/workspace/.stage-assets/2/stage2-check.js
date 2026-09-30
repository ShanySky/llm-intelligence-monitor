const { saveOrder } = require("./frontend/orderEditor");
const { AuditSink } = require("./backend/auditSink");
const { OrderService } = require("./backend/orderService");

(async()=>{
  const audit=new AuditSink();
  const service=new OrderService(audit);
  service.seed("c","base",1);
  service.patch({id:"c",expectedVersion:1,operationId:"remote",value:"remote"});
  const api={patch:async r=>service.patch(r),get:async id=>service.get(id)};
  const state={id:"c",value:"local-draft",version:1};
  let conflict=false;
  try { await saveOrder(api,state,{value:"local"}); }
  catch(e){ conflict=e&&e.code==="CONFLICT"; }
  if(!conflict) throw new Error("conflict not surfaced");
  const row=service.get("c");
  if(row.version!==2||row.value!=="remote") throw new Error("remote edit overwritten");
  if(state.version!==1||state.value!=="local-draft") throw new Error("local state advanced without confirmed save");
  console.log("STAGE2_PASS");
})().catch(e=>{console.error(e);process.exit(1);});
