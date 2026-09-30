const { OfflineQueue } = require("./frontend/offlineQueue");
const { MemoryQueueStorage } = require("./frontend/memoryQueueStorage");
const { AuditSink } = require("./backend/auditSink");
const { OrderService } = require("./backend/orderService");
const { ApiError } = require("./backend/errors");

(async()=>{
  const audit=new AuditSink();
  let crash=true;
  const service=new OrderService(audit,{afterCommit(){if(crash){crash=false;throw new ApiError("PROCESS_CRASH","process died after commit");}}});
  service.seed("q","draft",1);
  const api={patch:async r=>service.patch(r),get:async id=>service.get(id)};
  const storage=new MemoryQueueStorage();
  const q1=new OfflineQueue(storage);
  q1.enqueue({id:"q",value:"draft",version:1},{value:"ready"});
  try { await q1.flush(api); } catch(e) {}
  if(storage.items.length!==1) throw new Error("queue item lost before acknowledgement");

  const q2=new OfflineQueue(storage);
  await q2.flush(api);
  if(storage.items.length!==0) throw new Error("queue did not drain after restart");
  const row=service.get("q");
  if(row.version!==2||row.value!=="ready"||audit.count()!==1) throw new Error("restart replay did not converge");

  const q3=new OfflineQueue(storage);
  q3.enqueue({id:"q",value:"ready",version:2},{value:"v3"});
  q3.enqueue({id:"q",value:"v3",version:3},{value:"v4"});
  await q3.flush(api);
  if(service.get("q").version!==4||service.get("q").value!=="v4"||audit.count()!==3) throw new Error("separate queued edits collapsed");
  console.log("STAGE3_PASS");
})().catch(e=>{console.error(e);process.exit(1);});
