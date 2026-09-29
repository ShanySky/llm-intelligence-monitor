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
    steps=plan.get("steps",[]) if isinstance(plan,dict) else []
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
    add("async_visibility_race",15,"async" in review and "commit" in review and ("race" in review or "visibility" in review or "uncommitted" in review))
    add("order_scoped_inventory_idempotency",20,("order" in review and "idempot" in review) and ("event" in review or "different event" in review))
    add("random_audit_id_breaks_retry",15,("uuid" in review or "random" in review) and ("audit" in review or "retry" in review or "idempot" in review))
    add("after_commit_or_outbox_direction",15,("after commit" in review or "after_commit" in review or "outbox" in review or "transactional event" in review))
    add("requests_changes",5,"verdict: request_changes" in review)

else:
    raise SystemExit(f"unknown task {task}")

score=max(0,min(100,score))
result={"task":task,"score":score,"checks":checks}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
