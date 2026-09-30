#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path

root=Path(sys.argv[1]).resolve()
json_mode="--json" in sys.argv[2:]

hidden=r'''import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

public final class FrontierDeepFixHiddenTest {
  public static void main(String[] args) throws Exception {
    run("OPTIMISTIC", FrontierDeepFixHiddenTest::optimisticGate);
    run("TX", FrontierDeepFixHiddenTest::transactionBoundary);
    run("AUDIT_SNAPSHOT", FrontierDeepFixHiddenTest::auditSnapshot);
    run("AUDIT_IDEMP", FrontierDeepFixHiddenTest::auditIdempotency);
    run("BUSINESS_ID", FrontierDeepFixHiddenTest::businessIdentity);
    run("CRASH_RETRY", FrontierDeepFixHiddenTest::crashRetry);
    run("LOCK_ORDER", FrontierDeepFixHiddenTest::lockOrder);
  }

  interface Case { void run() throws Exception; }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }

  static final class PriceRepo implements ProductRepository {
    ProductSnapshot row=new ProductSnapshot(1,1,new BigDecimal("10.00"));
    boolean forceReject=false;
    public ProductSnapshot find(long id){ return row; }
    public boolean updateIfVersion(long id,long expected,BigDecimal price){
      if(forceReject || row.version()!=expected) return false;
      row=new ProductSnapshot(id,expected+1,price);
      return true;
    }
  }

  static void optimisticGate() {
    PriceRepo repo=new PriceRepo(); repo.forceReject=true;
    int[] evicts={0}, audits={0};
    PriceService s=new PriceService(repo,id->evicts[0]++,w->audits[0]++);
    try { s.changePrice(1,1,new BigDecimal("12.00")); } catch(RuntimeException ignored) {}
    check(evicts[0]==0 && audits[0]==0);
    check(repo.row.version()==1);
  }

  static void transactionBoundary() {
    PriceRepo repo=new PriceRepo();
    boolean[] preCommit={false};
    ProductCache cache=id->{ if(TransactionHooks.active()) preCommit[0]=true; };
    AuditQueue audits=w->{ if(TransactionHooks.active()) preCommit[0]=true; };
    PriceService s=new PriceService(repo,cache,audits);
    TransactionHooks.runInTransaction(()->s.changePrice(1,1,new BigDecimal("12.00")));
    check(!preCommit[0]);
  }

  static AuditWork acceptedWork(PriceRepo repo) {
    List<AuditWork> q=new ArrayList<>();
    PriceService s=new PriceService(repo,id->{},q::add);
    TransactionHooks.runInTransaction(()->s.changePrice(1,1,new BigDecimal("12.00")));
    check(q.size()==1);
    return q.get(0);
  }

  static void auditSnapshot() {
    PriceRepo repo=new PriceRepo();
    AuditWork work=acceptedWork(repo);
    repo.row=new ProductSnapshot(1,3,new BigDecimal("99.00"));
    List<BigDecimal> prices=new ArrayList<>();
    AuditSink sink=(key,id,version,price)->prices.add(price);
    new AuditWorker(repo,sink).deliver(work);
    check(prices.size()==1 && new BigDecimal("12.00").equals(prices.get(0)));
  }

  static void auditIdempotency() {
    PriceRepo repo=new PriceRepo();
    AuditWork work=acceptedWork(repo);
    List<String> keys=new ArrayList<>();
    AuditSink sink=(key,id,version,price)->keys.add(key);
    AuditWorker worker=new AuditWorker(repo,sink);
    worker.deliver(work); worker.deliver(work);
    check(keys.size()==2 && keys.get(0).equals(keys.get(1)));
  }

  static final class Events implements EventRepository {
    final Set<String> ids=new HashSet<>();
    public synchronized boolean exists(String id){return ids.contains(id);}
    public synchronized void insert(String id){ids.add(id);}
  }
  static final class States implements OrderStateRepository {
    final Map<String,OrderState> rows=new HashMap<>();
    public synchronized OrderState getOrCreate(String id){return rows.computeIfAbsent(id,OrderState::new);}
  }
  static final class Fulfills implements FulfillmentRepository {
    final Map<String,Fulfillment> rows=new HashMap<>();
    public synchronized Fulfillment findOrCreate(String key,String orderId){
      return rows.computeIfAbsent(key,k->new Fulfillment(orderId));
    }
  }
  static final class Inventory implements InventoryClient {
    final Map<String,String> effects=new HashMap<>();
    int calls=0;
    public synchronized String reserve(String orderId,String key){
      calls++;
      return effects.computeIfAbsent(key,k->"res-"+effects.size());
    }
    int effectCount(){return effects.size();}
  }

  static WebhookService webhook(Events e,States s,Fulfills f,Inventory i,FailureInjector x){
    return new WebhookService(e,s,f,i,x);
  }

  static void businessIdentity() {
    Events e=new Events(); States s=new States(); Fulfills f=new Fulfills(); Inventory i=new Inventory();
    WebhookService w=webhook(e,s,f,i,FailureInjector.none());
    w.paid("evt-a","o1",7); w.paid("evt-b","o1",7);
    check(i.effectCount()==1);
    check(s.getOrCreate("o1").version==7);
  }

  static void crashRetry() {
    Events e=new Events(); States s=new States(); Fulfills f=new Fulfills(); Inventory i=new Inventory();
    AtomicBoolean once=new AtomicBoolean(true);
    WebhookService w=webhook(e,s,f,i,id->{if(once.getAndSet(false))throw new RuntimeException("crash");});
    try { w.paid("evt-x","o2",3); } catch(RuntimeException expected) {}
    check(i.effectCount()==1);
    w.paid("evt-x","o2",3);
    check(i.effectCount()==1);
    Fulfillment row=f.rows.values().stream().filter(x->x.orderId.equals("o2")).findFirst().orElse(null);
    check(row!=null && row.completed && row.reservationKey!=null);
  }

  static final class Locks implements AccountLocks {
    final List<Long> acquired=new ArrayList<>();
    public AutoCloseable lock(long id){
      acquired.add(id);
      return ()->{};
    }
  }

  static void lockOrder() throws Exception {
    Locks locks=new Locks();
    ReservationMover m=new ReservationMover(locks);
    m.move(9,3);
    check(locks.acquired.equals(List.of(3L,9L)));
    locks.acquired.clear();
    m.cancelPair(9,3);
    check(locks.acquired.equals(List.of(3L,9L)));
  }

  static void check(boolean ok){if(!ok)throw new AssertionError();}
}'''

result={
  "compiles":False,
  "visible":False,
  "cases":{k:False for k in ["OPTIMISTIC","TX","AUDIT_SNAPSHOT","AUDIT_IDEMP","BUSINESS_ID","CRASH_RETRY","LOCK_ORDER"]},
  "raw_output":"",
  "compiler_output":""
}

with tempfile.TemporaryDirectory(prefix="frontier-deep-fix-") as td:
    td=Path(td)
    test=td/"FrontierDeepFixHiddenTest.java"
    test.write_text(hidden)
    src=sorted((root/"src").glob("*.java"))
    cp=subprocess.run(["javac","-d",str(td),*map(str,src),str(test)],capture_output=True,text=True)
    result["compiler_output"]=(cp.stdout or "")+(cp.stderr or "")
    result["compiles"]=cp.returncode==0
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(td),"VisibleTest"],capture_output=True,text=True)
        result["visible"]=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(td),"FrontierDeepFixHiddenTest"],capture_output=True,text=True,timeout=30)
        raw=(hr.stdout or "")+(hr.stderr or "")
        result["raw_output"]=raw
        for name in result["cases"]:
            result["cases"][name]=f"{name}_PASS" in raw

if json_mode:
    print(json.dumps(result))
    raise SystemExit(0 if result["compiles"] else 2)

if not result["compiles"]:
    print("VALIDATION_FAIL compile: repository no longer compiles")
    raise SystemExit(1)

messages=[
 ("OPTIMISTIC","optimistic conflict still triggers downstream work"),
 ("TX","cache or audit work still occurs before transaction commit"),
 ("AUDIT_SNAPSHOT","audit payload no longer represents the accepted price version"),
 ("AUDIT_IDEMP","audit retries do not reuse one business idempotency key"),
 ("BUSINESS_ID","different delivery events can duplicate one business fulfillment"),
 ("CRASH_RETRY","retry after external success does not converge to one completed fulfillment"),
 ("LOCK_ORDER","pair operations still acquire locks in inconsistent order"),
]
for key,msg in messages:
    if not result["cases"][key]:
        print(f"VALIDATION_FAIL {key.lower()}: {msg}")
        raise SystemExit(1)

print("VALIDATION_PASS: optimistic writes, transaction visibility, audit recovery, fulfillment recovery, and lock ordering are correct")
