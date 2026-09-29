import json, os, re, subprocess, sys
from pathlib import Path

task = sys.argv[1]
root = Path(sys.argv[2]).resolve()
out = Path(sys.argv[3]).resolve()
score = 0
checks = {}

def add(name, points, ok):
    global score
    ok = bool(ok)
    checks[name] = {"points": points, "passed": ok}
    if ok:
        score += points

def text(path):
    p = root / path
    return p.read_text(errors="replace") if p.exists() else ""

if task == "micro-export":
    hidden = r'''import java.util.concurrent.atomic.AtomicBoolean;
public final class HiddenTest {
  public static void main(String[] args) {
    int failed=0;
    try { cancelTest(); System.out.println("CHECK_CANCEL_PASS"); } catch(Throwable t) { failed++; System.out.println("CHECK_CANCEL_FAIL:"+t); }
    try { retryTest(); System.out.println("CHECK_RETRY_PASS"); } catch(Throwable t) { failed++; System.out.println("CHECK_RETRY_FAIL:"+t); }
    try { noRegenerateTest(); System.out.println("CHECK_NOREGEN_PASS"); } catch(Throwable t) { failed++; System.out.println("CHECK_NOREGEN_FAIL:"+t); }
    if (failed>0) System.exit(1);
  }
  static void cancelTest() {
    JobRepository jobs=new JobRepository(); ArtifactStore a=new ArtifactStore(); ExportService s=new ExportService(jobs,a,FailureInjector.none());
    String id="cancel-hidden-731"; jobs.create(id);
    s.run(id,new ReportGenerator(){ public int chunkCount(){return 5;} public String chunk(int i){ if(i==2)s.requestCancel(id); return "Q"+i; }});
    ExportJob j=jobs.get(id); check(j.state()==ExportJob.State.CANCELLED); check(j.artifactKey()==null); check(a.countForJob(id)==0);
  }
  static void retryTest() {
    JobRepository jobs=new JobRepository(); ArtifactStore a=new ArtifactStore(); AtomicBoolean once=new AtomicBoolean(true);
    ExportService s=new ExportService(jobs,a,id->{if(once.getAndSet(false)) throw new RuntimeException("crash");});
    String id="retry-hidden-419"; jobs.create(id);
    ReportGenerator g=new ReportGenerator(){ public int chunkCount(){return 2;} public String chunk(int i){return new String[]{"L","M"}[i];}};
    try{s.run(id,g);}catch(RuntimeException expected){}
    check(a.countForJob(id)==1); s.run(id,g); ExportJob j=jobs.get(id); check(j.state()==ExportJob.State.COMPLETED); check(a.countForJob(id)==1); check(j.artifactKey()!=null); check("LM".equals(a.get(j.artifactKey())));
  }
  static void noRegenerateTest() {
    JobRepository jobs=new JobRepository(); ArtifactStore a=new ArtifactStore(); AtomicBoolean once=new AtomicBoolean(true);
    ExportService s1=new ExportService(jobs,a,id->{if(once.getAndSet(false)) throw new RuntimeException("crash");});
    String id="noregen-hidden-863"; jobs.create(id);
    ReportGenerator first=new ReportGenerator(){ public int chunkCount(){return 1;} public String chunk(int i){return "ORIGINAL";}};
    try{s1.run(id,first);}catch(RuntimeException expected){}
    ExportService s2=new ExportService(jobs,a,FailureInjector.none());
    ReportGenerator forbidden=new ReportGenerator(){ public int chunkCount(){throw new AssertionError("regenerated");} public String chunk(int i){throw new AssertionError("regenerated");}};
    s2.run(id,forbidden); check(jobs.get(id).state()==ExportJob.State.COMPLETED); check(a.countForJob(id)==1);
  }
  static void check(boolean x){if(!x)throw new AssertionError();}
}'''
    (root/"HiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"HiddenTest.java")],capture_output=True,text=True)
    add("compiles",10,cp.returncode==0)
    visible_ok=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True)
        visible_ok=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"HiddenTest"],capture_output=True,text=True)
        hidden_out=hr.stdout+hr.stderr
    add("visible_regression",10,visible_ok)
    add("midflight_cancellation",30,"CHECK_CANCEL_PASS" in hidden_out)
    add("post_publish_retry",30,"CHECK_RETRY_PASS" in hidden_out)
    add("retry_without_regeneration",20,"CHECK_NOREGEN_PASS" in hidden_out)

elif task == "micro-incident":
    state=text(".state")
    actions=[x.strip() for x in text(".actions").splitlines() if x.strip()]
    report=text("REPORT.txt").lower()
    action_words="\n".join(actions)
    add("targeted_fix_applied",30,"stale=0" in state)
    add("within_action_budget",10,len(actions)<=7)
    add("gathered_revision_evidence",10,any(x.startswith("revisions") for x in actions))
    add("gathered_failure_evidence",10,any(x.startswith("logs api-5cc-old") for x in actions))
    add("checked_schema_or_pods",10,any(x.startswith("schema") or x.startswith("pods") for x in actions))
    add("avoided_speculative_restart_scale",10,"restart-all" not in action_words and not any(x.startswith("scale") for x in actions))
    add("verified_recovery",10,any(x.startswith("verify") for x in actions))
    add("root_cause_report",10,("stale" in report or "v1" in report) and ("schema" in report or "column" in report or "coupon" in report))

elif task == "micro-plan":
    try: plan=json.loads(text("plan.json")); valid=True
    except Exception: plan={}; valid=False
    add("valid_plan_json",10,valid)
    steps=plan.get("steps",[]) if isinstance(plan,dict) else []
    required=["S1","S3","S4","S5","S7","S8","S9","S10","S12"]
    unsafe={"S2","S6","S11","S13","S14"}
    for s in required:
        add("required_"+s,5,s in steps)
    add("no_unsafe_steps",15,not any(s in unsafe for s in steps))
    def before(a,b):
        return a in steps and b in steps and steps.index(a)<steps.index(b)
    add("safe_phase_order",10,before("S1","S3") and before("S3","S5") and before("S5","S7") and before("S8","S9") and before("S9","S10") and before("S10","S12"))
    inv=" ".join(map(str,plan.get("invariants",[]))).lower()
    val=" ".join(map(str,plan.get("validation",[]))).lower()
    add("states_compatibility_invariant",10,("v1" in inv and "v2" in inv) or "rollback" in inv or "compat" in inv)
    add("states_validation_gates",10,("parity" in val or "compare" in val) and ("rollback" in val or "v1" in val))

elif task == "micro-review":
    review=text("REVIEW.md").lower()
    add("self_invocation_async_proxy",20,("self-invocation" in review or "self invocation" in review or "proxy" in review) and "async" in review)
    add("cache_evict_before_commit",25,("cache" in review and "commit" in review and ("repopulate" in review or "stale" in review or "before" in review)))
    add("async_commit_visibility_race",20,("async" in review and "commit" in review and ("race" in review or "visible" in review or "visibility" in review)))
    add("after_commit_direction",20,("after commit" in review or "after_commit" in review or "transactionaleventlistener" in review or "transactional event" in review))
    add("audit_idempotency",10,("idempot" in review or "stable" in review) and ("audit" in review or "event" in review))
    add("requests_changes",5,"verdict: request_changes" in review)

elif task == "hard-plan":
    try: plan=json.loads(text("plan.json")); valid=True
    except Exception: plan={}; valid=False
    add("valid_plan_json",10,valid)
    raw_steps=plan.get("steps",[]) if isinstance(plan,dict) else []
    steps=[x if isinstance(x,str) else x.get("id") for x in raw_steps if isinstance(x,str) or isinstance(x,dict)]
    required=["P1","P2","P3","P4","P5","P6","P7","P8"]
    unsafe={"P9","P10","P11","P12","P13","P14"}
    for s in required:
        add("required_"+s,6,s in steps)
    add("no_unsafe_steps",12,not any(s in unsafe for s in steps))
    def before(a,b):
        return a in steps and b in steps and steps.index(a)<steps.index(b)
    add("safe_rollout_order",12,before("P1","P3") and before("P3","P2") and before("P2","P6") and before("P4","P7") and before("P5","P7") and before("P6","P7") and before("P7","P8"))
    inv=" ".join(map(str,plan.get("invariants",[]))).lower()
    val=" ".join(map(str,plan.get("validation",[]))).lower()
    add("compatibility_invariant",8,("consumer" in inv or "rollback" in inv or "both" in inv) and ("legacy" in inv or "customer_id" in inv or "compat" in inv))
    add("validation_depth",10,("unique" in val or "coverage" in val or "parity" in val) and ("rollback" in val or "consumer" in val))

elif task == "hard-webhook":
    hidden = r'''import java.util.concurrent.atomic.AtomicBoolean;
public final class HiddenWebhookTest {
  public static void main(String[] args) {
    int failed=0;
    try { sameEvent(); System.out.println("SAME_PASS"); } catch(Throwable t){failed++;System.out.println("SAME_FAIL:"+t);}
    try { differentEventSameOrder(); System.out.println("ORDER_PASS"); } catch(Throwable t){failed++;System.out.println("ORDER_FAIL:"+t);}
    try { crashRetry(); System.out.println("CRASH_PASS"); } catch(Throwable t){failed++;System.out.println("CRASH_FAIL:"+t);}
    if(failed>0)System.exit(1);
  }
  static void sameEvent(){
    EventLog e=new EventLog(); FulfillmentRepo r=new FulfillmentRepo(); InventoryClient i=new InventoryClient(); WebhookService s=new WebhookService(e,r,i,FailureInjector.none());
    s.paid("evt-a","order-9"); s.paid("evt-a","order-9"); check(e.size()==1); check(i.reservationCount()==1);
  }
  static void differentEventSameOrder(){
    EventLog e=new EventLog(); FulfillmentRepo r=new FulfillmentRepo(); InventoryClient i=new InventoryClient(); WebhookService s=new WebhookService(e,r,i,FailureInjector.none());
    s.paid("evt-a","order-4"); s.paid("evt-b","order-4"); check(e.size()==2); check(i.reservationCount()==1); Fulfillment f=r.get("order-4"); check(f!=null && f.completed);
  }
  static void crashRetry(){
    EventLog e=new EventLog(); FulfillmentRepo r=new FulfillmentRepo(); InventoryClient i=new InventoryClient(); AtomicBoolean once=new AtomicBoolean(true);
    WebhookService s=new WebhookService(e,r,i,id->{if(once.getAndSet(false))throw new RuntimeException("crash");});
    try{s.paid("evt-x","order-7");}catch(RuntimeException expected){}
    check(i.reservationCount()==1);
    s.paid("evt-x","order-7");
    check(i.reservationCount()==1); Fulfillment f=r.get("order-7"); check(f!=null && f.completed && f.reservationKey!=null);
  }
  static void check(boolean x){if(!x)throw new AssertionError();}
}'''
    (root/"HiddenWebhookTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"HiddenWebhookTest.java")],capture_output=True,text=True)
    add("compiles",10,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"HiddenWebhookTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",10,visible)
    add("same_event_duplicate",20,"SAME_PASS" in hidden_out)
    add("different_event_same_order",30,"ORDER_PASS" in hidden_out)
    add("post_reserve_crash_retry",30,"CRASH_PASS" in hidden_out)

elif task == "hard-incident":
    state=text(".state")
    actions=[x.strip() for x in text(".actions").splitlines() if x.strip()]
    report=text("REPORT.txt").lower()
    joined="\n".join(actions)
    add("targeted_replacement",30,"bad=0" in state and any(x.startswith("replace api-c") for x in actions))
    add("within_budget",10,len(actions)<=8)
    add("checked_failure_log",10,any(x.startswith("logs api-c") for x in actions))
    add("checked_pod_config",15,any(x.startswith("pod-config api-c") for x in actions))
    add("checked_current_configmap",10,any(x.startswith("configmap") for x in actions))
    add("avoided_restart_scale",10,"restart-all" not in joined and not any(x.startswith("scale") for x in actions))
    add("verified",10,any(x.startswith("verify") for x in actions))
    add("reported_config_drift",5,("config" in report or "generation" in report) and ("api-c" in report or "drift" in report or "legacy" in report))

elif task == "hard-review":
    review=text("REVIEW.md").lower()
    add("self_invocation_async",15,("self-invocation" in review or "self invocation" in review or "proxy" in review) and "async" in review)
    add("cache_before_commit",15,"cache" in review and "commit" in review and ("stale" in review or "repopulate" in review or "before" in review))
    add("order_scoped_inventory_idempotency",20,("order" in review and "idempot" in review) and ("event" in review or "different event" in review))
    add("random_audit_id_breaks_retry",15,("uuid" in review or "random" in review or "stable" in review) and ("audit" in review or "retry" in review or "idempot" in review))
    durable=("outbox" in review or "durable handoff" in review or "persist fulfillment" in review or "persist a" in review)
    after_commit=("after commit" in review or "after_commit" in review or "same transaction" in review or "transactionally" in review)
    add("durable_after_commit_handoff",30,durable and after_commit)
    add("requests_changes",5,"verdict: request_changes" in review)



elif task == "frontier-scheduler":
    hidden = r'''import java.util.*;
public final class FrontierSchedulerHiddenTest {
  public static void main(String[] args) {
    run("CRITICAL", FrontierSchedulerHiddenTest::criticalPath);
    run("DEPENDENCIES", FrontierSchedulerHiddenTest::dependencies);
    run("GPU", FrontierSchedulerHiddenTest::gpuExclusive);
    run("TIE", FrontierSchedulerHiddenTest::tieAndInputOrder);
    run("INVALID", FrontierSchedulerHiddenTest::invalidInputs);
  }
  interface Case { void run(); }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }
  static Map<String,ScheduleEntry> map(List<ScheduleEntry> xs) {
    Map<String,ScheduleEntry> m=new HashMap<>();
    for(ScheduleEntry e:xs) {
      if(m.put(e.id(),e)!=null) throw new AssertionError("duplicate schedule entry");
      check(e.end()-e.start()>0);
    }
    return m;
  }
  static int makespan(List<ScheduleEntry> xs) {
    return xs.stream().mapToInt(ScheduleEntry::end).max().orElse(0);
  }
  static void starts(Map<String,ScheduleEntry> m, Object... kv) {
    for(int i=0;i<kv.length;i+=2) check(m.get((String)kv[i]).start()==(Integer)kv[i+1]);
  }
  static void criticalPath() {
    Scheduler s=new Scheduler();
    List<Task> ts=List.of(
      new Task("A",4,List.of(),false),
      new Task("B",4,List.of(),false),
      new Task("Z",10,List.of(),false));
    List<ScheduleEntry> p=s.plan(ts,2); Map<String,ScheduleEntry> m=map(p);
    check(makespan(p)==10);
    starts(m,"A",0,"B",4,"Z",0);
    check(m.get("A").worker()==0);
    check(m.get("Z").worker()==1);
    check(m.get("B").worker()==0);
  }
  static void dependencies() {
    Scheduler s=new Scheduler();
    List<Task> ts=List.of(
      new Task("E",5,List.of("C","D"),false),
      new Task("C",6,List.of("B"),false),
      new Task("A",4,List.of(),false),
      new Task("D",3,List.of("A"),false),
      new Task("B",2,List.of(),false));
    List<ScheduleEntry> p=s.plan(ts,2); Map<String,ScheduleEntry> m=map(p);
    check(makespan(p)==13);
    starts(m,"A",0,"B",0,"C",2,"D",4,"E",8);
  }
  static void gpuExclusive() {
    Scheduler s=new Scheduler();
    List<Task> ts=List.of(
      new Task("A",5,List.of(),true),
      new Task("B",4,List.of(),true),
      new Task("C",6,List.of(),false),
      new Task("D",3,List.of("A"),false),
      new Task("E",2,List.of("B"),false));
    List<ScheduleEntry> p=s.plan(ts,2); Map<String,ScheduleEntry> m=map(p);
    check(makespan(p)==11);
    starts(m,"A",0,"B",5,"C",0,"D",6,"E",9);
    ScheduleEntry a=m.get("A"), b=m.get("B");
    check(a.end()<=b.start() || b.end()<=a.start());
  }
  static void tieAndInputOrder() {
    Scheduler s=new Scheduler();
    List<Task> one=List.of(
      new Task("C",2,List.of(),false),
      new Task("A",2,List.of(),false),
      new Task("B",2,List.of(),false));
    List<Task> two=List.of(
      new Task("B",2,List.of(),false),
      new Task("C",2,List.of(),false),
      new Task("A",2,List.of(),false));
    Map<String,ScheduleEntry> a=map(s.plan(one,2));
    Map<String,ScheduleEntry> b=map(s.plan(two,2));
    starts(a,"A",0,"B",0,"C",2);
    starts(b,"A",0,"B",0,"C",2);
  }
  static void invalidInputs() {
    Scheduler s=new Scheduler();
    expectBad(()->s.plan(List.of(new Task("A",1,List.of("X"),false)),1));
    expectBad(()->s.plan(List.of(new Task("A",1,List.of(),false),new Task("A",2,List.of(),false)),1));
    expectBad(()->s.plan(List.of(new Task("A",1,List.of("B"),false),new Task("B",1,List.of("A"),false)),1));
    expectBad(()->s.plan(List.of(new Task("A",0,List.of(),false)),1));
    expectBad(()->s.plan(List.of(new Task("A",1,List.of(),false)),0));
  }
  interface Bad { void run(); }
  static void expectBad(Bad b) {
    boolean ok=false; try{b.run();}catch(IllegalArgumentException e){ok=true;} check(ok);
  }
  static void check(boolean x){if(!x) throw new AssertionError();}
}'''
    (root/"FrontierSchedulerHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"FrontierSchedulerHiddenTest.java")],capture_output=True,text=True)
    add("compiles",10,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierSchedulerHiddenTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",10,visible)
    add("global_optimality_critical_path",25,"CRITICAL_PASS" in hidden_out)
    add("precedence_global_optimality",20,"DEPENDENCIES_PASS" in hidden_out)
    add("exclusive_gpu_resource",15,"GPU_PASS" in hidden_out)
    add("deterministic_tie_break",10,"TIE_PASS" in hidden_out)
    add("input_validation_and_cycle",10,"INVALID_PASS" in hidden_out)


elif task == "frontier-webhook":
    hidden = r'''import java.util.concurrent.atomic.AtomicBoolean;
public final class FrontierWebhookHiddenTest {
  public static void main(String[] args) {
    run("SAME", FrontierWebhookHiddenTest::sameEvent);
    run("ORDER", FrontierWebhookHiddenTest::differentEventSameOrder);
    run("CRASH", FrontierWebhookHiddenTest::crashRetry);
    run("CONCURRENT", FrontierWebhookHiddenTest::concurrentPaid);
    run("CANCEL", FrontierWebhookHiddenTest::cancelRelease);
    run("STALE", FrontierWebhookHiddenTest::stalePaidAfterCancel);
    run("REPAID", FrontierWebhookHiddenTest::newerPaidAfterCancel);
  }
  interface Case { void run() throws Exception; }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }
  static WebhookService service(EventLog e,FulfillmentRepo f,OrderStateRepo s,InventoryClient i,FailureInjector x) {
    return new WebhookService(e,f,s,i,x);
  }
  static void sameEvent() {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient();
    WebhookService s=service(e,f,st,i,FailureInjector.none());
    s.paid("evt-a","order-1",1); s.paid("evt-a","order-1",1);
    check(e.size()==1); check(i.reservationCount()==1); check("PAID".equals(st.get("order-1").status));
  }
  static void differentEventSameOrder() {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient();
    WebhookService s=service(e,f,st,i,FailureInjector.none());
    s.paid("evt-a","order-2",1); s.paid("evt-b","order-2",1);
    check(e.size()==2); check(i.reservationCount()==1); check("PAID".equals(st.get("order-2").status));
  }
  static void crashRetry() {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient(); AtomicBoolean once=new AtomicBoolean(true);
    WebhookService s=service(e,f,st,i,id->{if(once.getAndSet(false)) throw new RuntimeException("crash");});
    try{s.paid("evt-x","order-3",2);}catch(RuntimeException expected){}
    check(i.reservationCount()==1);
    s.paid("evt-x","order-3",2);
    check(i.reservationCount()==1); check("PAID".equals(st.get("order-3").status));
    Fulfillment row=f.get("order-3"); check(row!=null && row.completed && row.reservationKey!=null);
  }
  static void concurrentPaid() throws Exception {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient();
    WebhookService s=service(e,f,st,i,FailureInjector.none());
    Thread a=new Thread(()->s.paid("evt-c1","order-4",5));
    Thread b=new Thread(()->s.paid("evt-c2","order-4",5));
    a.start(); b.start(); a.join(); b.join();
    check(i.reservationCount()==1); check("PAID".equals(st.get("order-4").status));
  }
  static void cancelRelease() {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient();
    WebhookService s=service(e,f,st,i,FailureInjector.none());
    s.paid("evt-p","order-5",2); s.cancelled("evt-c","order-5",3);
    check(i.reservationCount()==0); check("CANCELLED".equals(st.get("order-5").status)); check(st.get("order-5").version==3);
  }
  static void stalePaidAfterCancel() {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient();
    WebhookService s=service(e,f,st,i,FailureInjector.none());
    s.paid("evt-p","order-6",2); s.cancelled("evt-c","order-6",4); s.paid("evt-stale","order-6",3);
    check(i.reservationCount()==0); check("CANCELLED".equals(st.get("order-6").status)); check(st.get("order-6").version==4);
  }
  static void newerPaidAfterCancel() {
    EventLog e=new EventLog(); FulfillmentRepo f=new FulfillmentRepo(); OrderStateRepo st=new OrderStateRepo(); InventoryClient i=new InventoryClient();
    WebhookService s=service(e,f,st,i,FailureInjector.none());
    s.paid("evt-p","order-7",2); s.cancelled("evt-c","order-7",3); s.paid("evt-p2","order-7",4);
    check(i.reservationCount()==1); check("PAID".equals(st.get("order-7").status)); check(st.get("order-7").version==4);
  }
  static void check(boolean x){if(!x) throw new AssertionError();}
}'''
    (root/"FrontierWebhookHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"FrontierWebhookHiddenTest.java")],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierWebhookHiddenTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("same_event_duplicate",10,"SAME_PASS" in hidden_out)
    add("different_event_same_order",15,"ORDER_PASS" in hidden_out)
    add("post_reserve_crash_retry",20,"CRASH_PASS" in hidden_out)
    add("concurrent_same_order",20,"CONCURRENT_PASS" in hidden_out)
    add("newer_cancel_releases",10,"CANCEL_PASS" in hidden_out)
    add("stale_paid_ignored",10,"STALE_PASS" in hidden_out)
    add("newer_paid_reactivates",5,"REPAID_PASS" in hidden_out)


elif task == "frontier-migration":
    hidden = r'''public final class FrontierMigrationHiddenTest {
  public static void main(String[] args) {
    run("FALLBACK", FrontierMigrationHiddenTest::legacyFallback);
    run("ROLLBACK", FrontierMigrationHiddenTest::v2ReadableByV1);
    run("V1NEWER", FrontierMigrationHiddenTest::newerV1VisibleToV2);
    run("BACKFILL", FrontierMigrationHiddenTest::backfillLegacy);
    run("STALE", FrontierMigrationHiddenTest::staleBackfillDoesNotClobber);
  }
  interface Case { void run(); }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }
  static void legacyFallback() {
    OrderStore s=new OrderStore(); V1OrderService v1=new V1OrderService(s); V2OrderService v2=new V2OrderService(s);
    v1.writeStatus("o1","NEW");
    check("NEW".equals(v2.readStatus("o1")));
  }
  static void v2ReadableByV1() {
    OrderStore s=new OrderStore(); V1OrderService v1=new V1OrderService(s); V2OrderService v2=new V2OrderService(s);
    v2.writeStatus("o2","PAID","card");
    check("PAID".equals(v1.readStatus("o2")));
  }
  static void newerV1VisibleToV2() {
    OrderStore s=new OrderStore(); V1OrderService v1=new V1OrderService(s); V2OrderService v2=new V2OrderService(s);
    v2.writeStatus("o3","PAID","card");
    v1.writeStatus("o3","CANCELLED");
    check("CANCELLED".equals(v2.readStatus("o3")));
  }
  static void backfillLegacy() {
    OrderStore s=new OrderStore(); V1OrderService v1=new V1OrderService(s); V2OrderService v2=new V2OrderService(s); BackfillJob b=new BackfillJob(s);
    v1.writeStatus("o4","SHIPPED");
    BackfillItem item=b.plan("o4"); b.apply(item);
    check("SHIPPED".equals(v2.readStatus("o4")));
    OrderRecord row=s.get("o4"); check(row.newVersion==row.legacyVersion);
  }
  static void staleBackfillDoesNotClobber() {
    OrderStore s=new OrderStore(); V1OrderService v1=new V1OrderService(s); V2OrderService v2=new V2OrderService(s); BackfillJob b=new BackfillJob(s);
    v1.writeStatus("o5","NEW");
    BackfillItem stale=b.plan("o5");
    v2.writeStatus("o5","PAID","card");
    b.apply(stale);
    check("PAID".equals(v2.readStatus("o5")));
    check("PAID".equals(v1.readStatus("o5")));
    OrderRecord row=s.get("o5"); check(row.newVersion>=2 && row.legacyVersion>=2);
  }
  static void check(boolean x){if(!x) throw new AssertionError();}
}'''
    (root/"FrontierMigrationHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"FrontierMigrationHiddenTest.java")],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierMigrationHiddenTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("legacy_fallback_read",15,"FALLBACK_PASS" in hidden_out)
    add("v2_write_rollback_compatible",20,"ROLLBACK_PASS" in hidden_out)
    add("newer_v1_write_visible_to_v2",20,"V1NEWER_PASS" in hidden_out)
    add("online_backfill_current_legacy",15,"BACKFILL_PASS" in hidden_out)
    add("stale_backfill_cannot_clobber_live_update",25,"STALE_PASS" in hidden_out)


elif task == "frontier-review":
    review=text("REVIEW.md").lower()

    # Score independent failure domains, not wording-specific subpoints.
    # Multiple technically equivalent phrasings count; overlapping symptoms do not
    # receive duplicate credit.
    add("cache_transaction_boundary",15,
        "cache" in review and
        ("commit" in review or "transaction" in review) and
        ("stale" in review or "repopulate" in review or "old committed" in review or "after commit" in review))

    audit_boundary = (
        "audit" in review and
        (
            ("self-invocation" in review or "self invocation" in review or ("proxy" in review and "async" in review))
            or
            ("outbox" in review or "after commit" in review or "durable" in review)
        )
    )
    audit_payload = (
        "audit" in review and
        ("re-read" in review or "reread" in review or "current" in review or "mutable" in review or "snapshot" in review)
        and
        ("later" in review or "different" in review or "version" in review or "expected" in review or "price" in review)
    )
    audit_key = (
        "audit" in review and
        ("uuid" in review or "random" in review or "stable" in review)
        and
        ("idempot" in review or "dedup" in review or "retry" in review or "key" in review)
    )
    add("audit_delivery_boundary",15,audit_boundary)
    add("audit_payload_and_idempotency",15,audit_payload and audit_key)

    order_scope = (
        "order" in review and "event" in review and
        ("idempot" in review or "fulfillment" in review or "reservation" in review) and
        ("key" in review or "scope" in review or "different event" in review or "per order" in review or "order-scoped" in review)
    )
    atomic_claim = (
        ("unique" in review or "atomic" in review or "lock" in review or "serialized" in review or "concurr" in review)
        and ("order" in review or "fulfillment" in review or "event" in review)
    )
    add("order_scoped_exactly_once",25,order_scope and atomic_claim)

    crash_recovery = (
        ("inventory" in review or "external" in review or "reservation" in review)
        and ("crash" in review or "failure" in review)
        and ("retry" in review or "reconcile" in review or "idempot" in review or "outbox" in review or "same key" in review)
    )
    add("external_side_effect_recovery",20,crash_recovery)

    add("requests_changes",10,"verdict: request_changes" in review)


elif task == "frontier-plan":
    plan=text("PLAN.md").lower()

    add("online_additive_schema",10,
        ("nullable" in plan or "additive" in plan) and
        ("online" in plan or "non-block" in plan or "lock" in plan or "ddl" in plan))

    stable_key = (
        ("stable" in plan or "persist" in plan or "stored" in plan) and
        ("uuid" in plan or "customer_key" in plan) and
        ("once" in plan or "never change" in plan or "immutable" in plan or "read" in plan)
    )
    add("stable_persisted_identity",10,stable_key)

    mixed_db = (
        ("v1" in plan and "v2" in plan) and
        ("dual" in plan or "compat" in plan or "fallback" in plan or "customer_id" in plan) and
        ("write" in plan or "read" in plan)
    )
    add("mixed_version_db_compatibility",15,mixed_db)

    backfill = (
        "backfill" in plan and
        ("batch" in plan or "resum" in plan or "checkpoint" in plan or "retry" in plan) and
        ("parity" in plan or "verify" in plan or "coverage" in plan or "unique" in plan)
    )
    add("resumable_verified_backfill",10,backfill)

    rest_jwt = (
        ("rest" in plan or "api" in plan) and
        ("jwt" in plan or "token" in plan) and
        ("both" in plan or "dual" in plan or "compat" in plan or "customer_id" in plan)
    )
    add("rest_and_jwt_compatibility",10,rest_jwt)

    kafka = (
        "kafka" in plan and
        ("customer_id" in plan and "customer_key" in plan) and
        ("additive" in plan or "both" in plan or "dual" in plan) and
        ("consumer" in plan or "partner" in plan)
    )
    add("kafka_consumer_first_compatibility",15,kafka)

    cache = (
        ("redis" in plan or "cache" in plan) and
        ("customer_id" in plan or "legacy" in plan or "v1" in plan) and
        ("invalidation" in plan or "key" in plan) and
        ("both" in plan or "dual" in plan or "compat" in plan or "keep" in plan or "bridge" in plan)
    )
    add("cache_and_invalidation_compatibility",15,cache)

    rollback = (
        "rollback" in plan and
        ("release" in plan or "window" in plan or "v1" in plan) and
        ("test" in plan or "verify" in plan or "gate" in plan or "drill" in plan)
    )
    add("rollback_gate",10,rollback)

    cleanup = (
        ("cleanup" in plan or "remove" in plan or "drop" in plan or "not null" in plan or "constraint" in plan) and
        ("later" in plan or "after" in plan) and
        ("rollback" in plan or "consumer" in plan or "window" in plan)
    )
    add("delayed_cleanup",5,cleanup)


elif task == "frontier-plan-review":
    raw=text("FINDINGS.json")
    try:
        data=json.loads(raw)
        valid=isinstance(data,dict) and isinstance(data.get("unsafe_steps"),list)
    except Exception:
        data={}
        valid=False
    add("valid_findings_json",10,valid)

    expected={"P04","P06","P08","P10","P12","P14"}
    reported=set()
    if valid:
        for x in data.get("unsafe_steps",[]):
            if isinstance(x,str):
                reported.add(x.strip().upper())

    for step in sorted(expected):
        add("found_"+step,15,step in reported)

    false_positives=sorted(reported-expected)
    if false_positives:
        score -= 10 * len(false_positives)
        checks["false_positive_penalty"]={
            "points": -10 * len(false_positives),
            "passed": False,
            "reported": false_positives
        }

else:
    raise SystemExit(f"unknown task {task}")

score=max(0,min(100,score))
result={"task":task,"score":score,"checks":checks}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
