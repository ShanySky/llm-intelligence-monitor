const { saveOrder } = require("./frontend/orderEditor");
const { AuditSink } = require("./backend/auditSink");
const { OrderService } = require("./backend/orderService");

(async()=>{
  const audit=new AuditSink();
  const service=new OrderService(audit);
  service.seed("o","draft",1);
  const api={patch:async r=>service.patch(r),get:async id=>service.get(id)};
  const state={id:"o",value:"draft",version:1};
  await saveOrder(api,state,{value:"ready"});
  if(state.value!=="ready"||state.version!==2||audit.count()!==1) throw new Error("visible");
  console.log("VISIBLE_TEST_PASS");
})().catch(e=>{console.error(e);process.exit(1);});
