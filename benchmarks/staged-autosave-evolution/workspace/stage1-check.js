const { saveOrder } = require("./frontend/orderEditor");
const { AuditSink } = require("./backend/auditSink");
const { OrderService } = require("./backend/orderService");
const { ApiError } = require("./backend/errors");

(async()=>{
  const audit=new AuditSink();
  let once=true;
  const service=new OrderService(audit,{afterCommit(){if(once){once=false;throw new ApiError("TIMEOUT","lost response");}}});
  service.seed("o","draft",1);
  const api={patch:async r=>service.patch(r),get:async id=>service.get(id)};
  const state={id:"o",value:"draft",version:1};
  const out=await saveOrder(api,state,{value:"ready"});
  if(out.version!==2||service.get("o").version!==2||audit.count()!==1) throw new Error("transport retry did not converge");
  console.log("STAGE1_PASS");
})().catch(e=>{console.error(e);process.exit(1);});
