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





elif task == "frontier-config":
    hidden = r'''import java.nio.file.*;
import java.util.*;
public final class FrontierConfigHiddenTest {
  public static void main(String[] args) throws Exception {
    run("LEGACY", FrontierConfigHiddenTest::legacyDefault);
    run("EXPLICIT", FrontierConfigHiddenTest::explicitSupported);
    run("INVALID", FrontierConfigHiddenTest::invalidRejected);
    run("ENV", FrontierConfigHiddenTest::environmentOverride);
    run("REGRESSION", FrontierConfigHiddenTest::existingFields);
  }
  interface Case { void run() throws Exception; }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }
  static Path props(String body) throws Exception {
    Path p=Files.createTempFile("frontier-config-hidden",".properties");
    Files.writeString(p,body);
    return p;
  }
  static void legacyDefault() throws Exception {
    Path p=props("logLevel=INFO\nport=8080\n");
    Config c=new ConfigLoader().load(p,Map.of());
    check("1.0".equals(c.version()));
    Files.deleteIfExists(p);
  }
  static void explicitSupported() throws Exception {
    Path p=props("version=1.0\nlogLevel=DEBUG\nport=8082\n");
    Config c=new ConfigLoader().load(p,Map.of());
    check("1.0".equals(c.version()));
    Files.deleteIfExists(p);
  }
  static void invalidRejected() throws Exception {
    Path p=props("version=2.0\n");
    expectBad(()->new ConfigLoader().load(p,Map.of()));
    Files.deleteIfExists(p);
  }
  static void environmentOverride() throws Exception {
    Path p=props("version=2.0\nport=7000\n");
    Config c=new ConfigLoader().load(p,Map.of("APP_VERSION","1.0","APP_PORT","7001"));
    check("1.0".equals(c.version())); check(c.port()==7001);
    expectBad(()->new ConfigLoader().load(p,Map.of("APP_VERSION","2.0")));
    Files.deleteIfExists(p);
  }
  static void existingFields() throws Exception {
    Path p=props("logLevel=WARN\nport=8123\n");
    Config c=new ConfigLoader().load(p,Map.of("APP_LOG_LEVEL","TRACE"));
    check("TRACE".equals(c.logLevel())); check(c.port()==8123);
    Files.deleteIfExists(p);
  }
  interface Bad { void run(); }
  static void expectBad(Bad b) {
    boolean ok=false; try{b.run();}catch(IllegalArgumentException e){ok=true;} check(ok);
  }
  static void check(boolean x){if(!x) throw new AssertionError();}
}'''
    (root/"FrontierConfigHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"FrontierConfigHiddenTest.java")],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierConfigHiddenTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("legacy_defaults_to_v1",15,"LEGACY_PASS" in hidden_out)
    add("explicit_v1_supported",10,"EXPLICIT_PASS" in hidden_out)
    add("unsupported_version_rejected",20,"INVALID_PASS" in hidden_out)
    add("environment_override_semantics",15,"ENV_PASS" in hidden_out)
    add("existing_config_regression",10,"REGRESSION_PASS" in hidden_out)

    generated_ok=False
    try:
        gr=subprocess.run(["bash","check_generated.sh"],cwd=root,capture_output=True,text=True,timeout=30)
        schema=json.loads(text("generated/config.schema.json"))
        prop=schema.get("properties",{}).get("version",{})
        examples=[text("examples/local.properties"),text("examples/production.properties")]
        generated_ok=(gr.returncode==0 and prop.get("type")=="string" and prop.get("default")=="1.0" and prop.get("enum")==["1.0"])
        examples_ok=all(re.search(r"(?m)^version\s*=\s*1\.0\s*$",x) for x in examples)
    except Exception:
        generated_ok=False; examples_ok=False
    add("schema_source_and_generated_contract",15,generated_ok)
    add("checked_in_examples_versioned",10,examples_ok)


elif task == "frontier-filter":
    hidden = r'''import java.util.*;
public final class FrontierFilterHiddenTest {
  public static void main(String[] args) {
    run("PRECEDENCE", FrontierFilterHiddenTest::precedence);
    run("NESTING", FrontierFilterHiddenTest::nesting);
    run("NULLS", FrontierFilterHiddenTest::nulls);
    run("ESCAPES", FrontierFilterHiddenTest::escapesAndIdentifiers);
    run("INVALID", FrontierFilterHiddenTest::invalid);
  }
  interface Case { void run(); }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }
  static void precedence() {
    FilterEngine e=new FilterEngine();
    Map<String,String> r=new HashMap<>();
    r.put("a","1"); r.put("b","0"); r.put("c","0");
    check(e.matches("a = \"1\" OR b = \"2\" AND c = \"3\"",r));
    r.put("a","0"); r.put("b","2"); r.put("c","3");
    check(e.matches("a = \"1\" OR b = \"2\" AND c = \"3\"",r));
    r.put("c","0");
    check(!e.matches("a = \"1\" OR b = \"2\" AND c = \"3\"",r));
  }
  static void nesting() {
    FilterEngine e=new FilterEngine();
    Map<String,String> r=new HashMap<>();
    r.put("role","admin"); r.put("tier","free"); r.put("active","yes");
    check(e.matches("NOT(role = \"guest\" OR(tier = \"free\" AND NOT active = \"yes\"))",r));
    check(e.matches("(role = \"admin\" AND active = \"yes\") OR role = \"owner\"",r));
    check(!e.matches("NOT NOT role != \"admin\"",r));
  }
  static void nulls() {
    FilterEngine e=new FilterEngine();
    Map<String,String> r=new HashMap<>();
    r.put("present","v"); r.put("explicit",null);
    check(e.matches("missing IS NULL",r));
    check(e.matches("explicit is null",r));
    check(e.matches("present IS NOT NULL",r));
    check(e.matches("missing != \"x\"",r));
    check(!e.matches("missing = \"x\"",r));
    check(!e.matches("present IS NULL",r));
  }
  static void escapesAndIdentifiers() {
    FilterEngine e=new FilterEngine();
    Map<String,String> r=new HashMap<>();
    r.put("name","a\"b\\c");
    r.put("user.role","ops");
    r.put("feature-flag","on");
    check(e.matches("name = \"a\\\"b\\\\c\"",r));
    check(e.matches("user.role = \"ops\" aNd feature-flag = \"on\"",r));
  }
  static void invalid() {
    FilterEngine e=new FilterEngine(); Map<String,String> r=new HashMap<>();
    expectBad(()->e.matches("",r));
    expectBad(()->e.matches("a = \"x\" AND",r));
    expectBad(()->e.matches("(a = \"x\"",r));
    expectBad(()->e.matches("a = \"x\" garbage",r));
    expectBad(()->e.matches("a = \"unterminated",r));
    expectBad(()->e.matches("a = \"bad\\n\"",r));
    expectBad(()->e.matches("a IS maybe",r));
  }
  interface Bad { void run(); }
  static void expectBad(Bad b) {
    boolean ok=false; try{b.run();}catch(IllegalArgumentException ex){ok=true;} check(ok);
  }
  static void check(boolean x){if(!x) throw new AssertionError();}
}'''
    (root/"FrontierFilterHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"FrontierFilterHiddenTest.java")],capture_output=True,text=True)
    add("compiles",10,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierFilterHiddenTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",10,visible)
    add("operator_precedence",20,"PRECEDENCE_PASS" in hidden_out)
    add("nested_parentheses_and_not",20,"NESTING_PASS" in hidden_out)
    add("null_and_missing_semantics",15,"NULLS_PASS" in hidden_out)
    add("escaped_strings_and_identifiers",15,"ESCAPES_PASS" in hidden_out)
    add("malformed_expression_rejection",10,"INVALID_PASS" in hidden_out)


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


elif task in ("frontier-webhook", "frontier-webhook-hidden"):
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


elif task == "frontier-incident-cascade":
    state={}
    for line in text(".state").splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            state[k.strip()]=v.strip()
    actions=[x.strip() for x in text(".actions").splitlines() if x.strip()]
    report=text("REPORT.txt").lower()

    def pos(prefix, start=0):
        for i,x in enumerate(actions[start:], start):
            if x == prefix or x.startswith(prefix+" "):
                return i
        return None

    config_fix=pos("replace-config")
    first_verify_after_config=pos("verify", (config_fix+1) if config_fix is not None else 0)
    consumer_fix=pos("replace-consumer")

    config_evidence=False
    if config_fix is not None:
        for x in actions[:config_fix]:
            if x == "pods" or x == "logs api-b" or x == "config api-b":
                config_evidence=True

    second_evidence=False
    if first_verify_after_config is not None and consumer_fix is not None and consumer_fix > first_verify_after_config:
        between=actions[first_verify_after_config+1:consumer_fix]
        second_evidence=("queue" in between and "logs consumer-2" in between)

    dangerous=any(
        x=="restart-all" or x.startswith("scale ") or x=="reset-offset"
        for x in actions
    )

    add("targeted_config_repair",20,state.get("config_bad")=="0")
    add("post_fix_verification_exposed_second_failure",15,state.get("staged_seen")=="1")
    add("targeted_consumer_repair",20,state.get("consumer_bad")=="0")
    add("config_evidence_before_mutation",10,config_evidence)
    add("second_stage_evidence_before_mutation",10,second_evidence)
    add("avoided_broad_or_destructive_actions",10,not dangerous)
    add("final_end_to_end_verification",10,state.get("final_verified")=="1")
    report_ok=(
        ("config" in report and ("drift" in report or "revision" in report))
        and ("consumer" in report and ("duplicate" in report or "dedup" in report or "contract" in report))
    )
    add("reported_both_failure_domains",5,report_ok)


elif task == "frontier-identity-rollout":
    hidden = r'''import java.util.*;
import java.util.concurrent.*;
public final class FrontierIdentityHiddenTest {
  public static void main(String[] args) {
    run("LEGACY_STABLE", FrontierIdentityHiddenTest::legacyGetsStableKey);
    run("CONCURRENT_STABLE", FrontierIdentityHiddenTest::concurrentLegacyAssignment);
    run("NO_ROTATE", FrontierIdentityHiddenTest::assignedKeyDoesNotRotate);
    run("V1_PRESERVE", FrontierIdentityHiddenTest::v1UpdatePreservesKey);
    run("REST", FrontierIdentityHiddenTest::restAdditive);
    run("JWT", FrontierIdentityHiddenTest::jwtAdditive);
    run("KAFKA", FrontierIdentityHiddenTest::kafkaAdditive);
    run("CACHE", FrontierIdentityHiddenTest::cacheFallback);
  }
  interface Case { void run() throws Exception; }
  static void run(String name, Case c) {
    try { c.run(); System.out.println(name+"_PASS"); }
    catch(Throwable t) { System.out.println(name+"_FAIL:"+t); }
  }
  static void legacyGetsStableKey() {
    CustomerStore s=new CustomerStore(); V1CustomerService v1=new V1CustomerService(s); IdentityService ids=new IdentityService(s);
    Customer c=v1.write(41L,"Legacy");
    String a=ids.customerKey(41L), b=ids.customerKey(41L);
    check(a!=null && !a.isBlank()); check(a.equals(b)); check(a.equals(c.customerKey));
  }
  static void concurrentLegacyAssignment() throws Exception {
    CustomerStore s=new CustomerStore(); V1CustomerService v1=new V1CustomerService(s); IdentityService ids=new IdentityService(s);
    Customer c=v1.write(42L,"Concurrent");
    int n=12;
    CountDownLatch ready=new CountDownLatch(n), go=new CountDownLatch(1);
    Set<String> seen=Collections.synchronizedSet(new HashSet<>());
    List<Thread> threads=new ArrayList<>();
    for(int i=0;i<n;i++){
      Thread t=new Thread(()->{
        try { ready.countDown(); go.await(); seen.add(ids.customerKey(42L)); }
        catch(InterruptedException e){ throw new RuntimeException(e); }
      });
      threads.add(t); t.start();
    }
    ready.await(); go.countDown();
    for(Thread t:threads)t.join();
    check(seen.size()==1);
    String only=seen.iterator().next();
    check(only!=null && only.equals(c.customerKey));
  }
  static void assignedKeyDoesNotRotate() {
    CustomerStore s=new CustomerStore(); IdentityService ids=new IdentityService(s); V2CustomerService v2=new V2CustomerService(s,ids);
    Customer a=v2.write(7L,"ck-original","A");
    Customer b=v2.write(7L,"ck-other","B");
    check("ck-original".equals(a.customerKey)); check("ck-original".equals(b.customerKey));
  }
  static void v1UpdatePreservesKey() {
    CustomerStore s=new CustomerStore(); IdentityService ids=new IdentityService(s); V1CustomerService v1=new V1CustomerService(s); V2CustomerService v2=new V2CustomerService(s,ids);
    Customer c=v2.write(8L,"ck-8","A"); v1.write(8L,"B");
    check("ck-8".equals(c.customerKey)); check(v1.id(c)==8L); check("B".equals(c.name));
  }
  static void restAdditive() {
    Customer c=new Customer(9L,"R"); c.customerKey="ck-9";
    String x=new RestContract().encode(c);
    check(x.contains("customer_id") && x.contains("9") && x.contains("customer_key") && x.contains("ck-9"));
  }
  static void jwtAdditive() {
    Customer c=new Customer(10L,"J"); c.customerKey="ck-10";
    String x=new JwtContract().claims(c);
    check(x.contains("customer_id") && x.contains("10") && x.contains("customer_key") && x.contains("ck-10"));
  }
  static void kafkaAdditive() {
    Customer c=new Customer(11L,"K"); c.customerKey="ck-11";
    String x=new KafkaContract().event(c);
    check(x.contains("customer_id") && x.contains("11") && x.contains("customer_key") && x.contains("ck-11"));
  }
  static void cacheFallback() {
    CustomerCache c=new CustomerCache();
    c.putLegacy(12L,"old");
    check("old".equals(c.getCompatible(12L,"ck-12")));
    c.putV2("ck-12","new");
    check("new".equals(c.getCompatible(12L,"ck-12")));
  }
  static void check(boolean x){if(!x)throw new AssertionError();}
}'''
    (root/"FrontierIdentityHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run(["javac","-d",str(outdir),*map(str,(root/"src").glob("*.java")),str(root/"FrontierIdentityHiddenTest.java")],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True); visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierIdentityHiddenTest"],capture_output=True,text=True); hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("legacy_key_stable_and_persisted",15,"LEGACY_STABLE_PASS" in hidden_out)
    add("concurrent_legacy_assignment_single_key",15,"CONCURRENT_STABLE_PASS" in hidden_out)
    add("assigned_key_never_rotates",15,"NO_ROTATE_PASS" in hidden_out)
    add("v1_update_preserves_v2_identity",10,"V1_PRESERVE_PASS" in hidden_out)
    add("rest_additive_contract",10,"REST_PASS" in hidden_out)
    add("jwt_additive_contract",10,"JWT_PASS" in hidden_out)
    add("kafka_additive_contract",7,"KAFKA_PASS" in hidden_out)
    add("cache_legacy_fallback_and_v2_preference",8,"CACHE_PASS" in hidden_out)


elif task == "frontier-outbox-recovery":
    hidden = r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public final class FrontierOutboxRecoveryHiddenTest {
  public static void main(String[] args) {
    run("ROLLBACK", FrontierOutboxRecoveryHiddenTest::rollbackIsAtomic);
    run("CONCURRENT", FrontierOutboxRecoveryHiddenTest::sameVersionIsOneLogicalEvent);
    run("CRASH_RETRY", FrontierOutboxRecoveryHiddenTest::crashAfterPublishDoesNotDuplicate);
    run("LEGACY", FrontierOutboxRecoveryHiddenTest::eventIsAdditiveForLegacyConsumer);
    run("VERSIONS", FrontierOutboxRecoveryHiddenTest::differentVersionsRemainDistinct);
    run("REDRAIN", FrontierOutboxRecoveryHiddenTest::sentRowsAreNotRepublished);
  }

  interface Case { void run() throws Exception; }

  static void run(String name, Case c) {
    try { c.run(); System.out.println(name + "_PASS"); }
    catch (Throwable t) { System.out.println(name + "_FAIL:" + t); }
  }

  static Database db(String id) {
    Database db = new Database();
    db.createOrder(id, "key-" + id);
    return db;
  }

  static void rollbackIsAtomic() {
    Database db = db("o-rb");
    OrderService service = new OrderService(db, new EventEncoder());
    FailureInjector fail = new FailureInjector() {
      @Override public void beforeOutbox(String orderId) {
        throw new RuntimeException("rollback");
      }
    };
    boolean threw = false;
    try { service.confirm("o-rb", 1, fail); }
    catch (RuntimeException expected) { threw = true; }
    check(threw);
    Order row = db.getOrder("o-rb");
    check(row != null);
    check("PENDING".equals(row.status));
    check(row.version == 0);
    check(db.outboxSize() == 0);
  }

  static void sameVersionIsOneLogicalEvent() throws Exception {
    Database db = db("o-con");
    OrderService service = new OrderService(db, new EventEncoder());
    CountDownLatch ready = new CountDownLatch(2);
    CountDownLatch go = new CountDownLatch(1);
    List<Throwable> errors = Collections.synchronizedList(new ArrayList<>());
    Runnable task = () -> {
      try {
        ready.countDown();
        go.await();
        service.confirm("o-con", 4, FailureInjector.none());
      } catch (Throwable t) {
        errors.add(t);
      }
    };
    Thread a = new Thread(task), b = new Thread(task);
    a.start(); b.start();
    ready.await(); go.countDown();
    a.join(); b.join();
    check(errors.isEmpty());
    check(db.outboxSize() == 1);
    Order row = db.getOrder("o-con");
    check(row != null && row.version == 4 && "CONFIRMED".equals(row.status));
  }

  static void crashAfterPublishDoesNotDuplicate() {
    Database db = db("o-crash");
    OrderService service = new OrderService(db, new EventEncoder());
    EventBroker broker = new EventBroker();
    OutboxWorker worker = new OutboxWorker(db, broker);
    service.confirm("o-crash", 2, FailureInjector.none());

    AtomicBoolean once = new AtomicBoolean(true);
    FailureInjector crash = new FailureInjector() {
      @Override public void afterPublish(String eventId) {
        if (once.getAndSet(false)) throw new RuntimeException("crash-after-publish");
      }
    };
    try { worker.drain(crash); }
    catch (RuntimeException expected) {}
    check(broker.deliveredCount() == 1);

    worker.drain(FailureInjector.none());
    check(broker.deliveredCount() == 1);
    check(db.pendingOutbox().isEmpty());
  }

  static void eventIsAdditiveForLegacyConsumer() {
    Database db = db("o-legacy");
    OrderService service = new OrderService(db, new EventEncoder());
    service.confirm("o-legacy", 3, FailureInjector.none());
    List<OutboxRecord> rows = db.pendingOutbox();
    check(rows.size() == 1);
    String payload = rows.get(0).payload;
    check(new LegacyOrderConsumer().accepts(payload));
    check(payload.contains("order_key:key-o-legacy"));
    check(payload.contains("version:3"));
  }

  static void differentVersionsRemainDistinct() {
    Database db = db("o-vers");
    OrderService service = new OrderService(db, new EventEncoder());
    EventBroker broker = new EventBroker();
    OutboxWorker worker = new OutboxWorker(db, broker);
    service.confirm("o-vers", 1, FailureInjector.none());
    service.confirm("o-vers", 2, FailureInjector.none());
    check(db.outboxSize() == 2);
    worker.drain(FailureInjector.none());
    check(broker.deliveredCount() == 2);
  }

  static void sentRowsAreNotRepublished() {
    Database db = db("o-redrain");
    OrderService service = new OrderService(db, new EventEncoder());
    EventBroker broker = new EventBroker();
    OutboxWorker worker = new OutboxWorker(db, broker);
    service.confirm("o-redrain", 1, FailureInjector.none());
    worker.drain(FailureInjector.none());
    worker.drain(FailureInjector.none());
    check(broker.deliveredCount() == 1);
    check(db.pendingOutbox().isEmpty());
  }

  static void check(boolean x) {
    if (!x) throw new AssertionError();
  }
}'''
    (root/"FrontierOutboxRecoveryHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run([
        "javac","-d",str(outdir),
        *map(str,(root/"src").glob("*.java")),
        str(root/"FrontierOutboxRecoveryHiddenTest.java")
    ],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True)
        visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierOutboxRecoveryHiddenTest"],capture_output=True,text=True)
        hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("transaction_rollback_keeps_order_and_outbox_atomic",20,"ROLLBACK_PASS" in hidden_out)
    add("concurrent_same_version_is_one_logical_event",15,"CONCURRENT_PASS" in hidden_out)
    add("crash_after_publish_retry_is_idempotent",25,"CRASH_RETRY_PASS" in hidden_out)
    add("event_contract_is_additive_for_legacy_consumer",15,"LEGACY_PASS" in hidden_out)
    add("different_versions_have_distinct_delivery_identity",10,"VERSIONS_PASS" in hidden_out)
    add("sent_outbox_rows_are_not_republished",5,"REDRAIN_PASS" in hidden_out)

elif task == "frontier-lease-fencing":
    hidden = r'''public final class FrontierLeaseFencingHiddenTest {
  public static void main(String[] args) {
    run("TOKEN", FrontierLeaseFencingHiddenTest::takeoverTokenIncreases);
    run("RENEW", FrontierLeaseFencingHiddenTest::staleRenewRejected);
    run("STALE", FrontierLeaseFencingHiddenTest::staleWorkerCannotCommit);
    run("CRASH_SAME", FrontierLeaseFencingHiddenTest::sameGenerationCrashRetry);
    run("CRASH_TAKEOVER", FrontierLeaseFencingHiddenTest::takeoverRetryReusesBusinessIdentity);
    run("CANCEL", FrontierLeaseFencingHiddenTest::cancelDuringEffectStaysAuthoritative);
  }

  interface Case { void run(); }

  static void run(String name, Case c) {
    try { c.run(); System.out.println(name + "_PASS"); }
    catch (Throwable t) { System.out.println(name + "_FAIL:" + t); }
  }

  static JobRunner runner(LeaseStore l, ResultStore r, CancellationStore c, BillingAdapter b) {
    return new JobRunner(l, r, c, b);
  }

  static void takeoverTokenIncreases() {
    LeaseStore l = new LeaseStore();
    Lease a = l.acquire("j", "a", 0, 10);
    Lease b = l.acquire("j", "b", 20, 10);
    check(b.token > a.token);
    check("b".equals(b.owner));
    check(l.currentToken("j") == b.token);
  }

  static void staleRenewRejected() {
    LeaseStore l = new LeaseStore();
    Lease a = l.acquire("j", "a", 0, 10);
    Lease b = l.acquire("j", "b", 20, 10);
    check(!l.renew("j", "a", a.token, 21, 10));
    check(!l.renew("j", "b", a.token, 21, 10));
    check(l.renew("j", "b", b.token, 21, 10));
  }

  static void staleWorkerCannotCommit() {
    LeaseStore l = new LeaseStore(); ResultStore r = new ResultStore();
    CancellationStore c = new CancellationStore(); BillingAdapter b = new BillingAdapter();
    JobRunner x = runner(l,r,c,b);
    Lease old = x.begin("j", "a", 0, 10);
    Lease fresh = x.begin("j", "b", 20, 10);
    x.finish("j", old, "OLD", FailureInjector.none());
    check(r.get("j") == null);
    check(b.effectCount() == 0);
    x.finish("j", fresh, "NEW", FailureInjector.none());
    check("NEW".equals(r.get("j")));
    check(r.token("j") == fresh.token);
    check(b.effectCount() == 1);
  }

  static void sameGenerationCrashRetry() {
    LeaseStore l = new LeaseStore(); ResultStore r = new ResultStore();
    CancellationStore c = new CancellationStore(); BillingAdapter b = new BillingAdapter();
    JobRunner x = runner(l,r,c,b);
    Lease lease = x.begin("j", "a", 0, 10);
    FailureInjector fail = new FailureInjector() {
      boolean once = true;
      @Override public void afterExternalEffect(String jobId, long token) {
        if (once) { once = false; throw new RuntimeException("crash"); }
      }
    };
    try { x.finish("j", lease, "DONE", fail); } catch (RuntimeException expected) {}
    check(b.effectCount() == 1);
    x.finish("j", lease, "DONE", FailureInjector.none());
    check(b.effectCount() == 1);
    check("DONE".equals(r.get("j")));
  }

  static void takeoverRetryReusesBusinessIdentity() {
    LeaseStore l = new LeaseStore(); ResultStore r = new ResultStore();
    CancellationStore c = new CancellationStore(); BillingAdapter b = new BillingAdapter();
    JobRunner x = runner(l,r,c,b);
    Lease first = x.begin("j", "a", 0, 10);
    try {
      x.finish("j", first, "DONE", new FailureInjector() {
        @Override public void afterExternalEffect(String jobId, long token) {
          throw new RuntimeException("crash");
        }
      });
    } catch (RuntimeException expected) {}
    check(b.effectCount() == 1);
    Lease second = x.begin("j", "b", 20, 10);
    x.finish("j", second, "DONE", FailureInjector.none());
    check(b.effectCount() == 1);
    check("DONE".equals(r.get("j")));
    check(r.token("j") == second.token);
  }

  static void cancelDuringEffectStaysAuthoritative() {
    LeaseStore l = new LeaseStore(); ResultStore r = new ResultStore();
    CancellationStore c = new CancellationStore(); BillingAdapter b = new BillingAdapter();
    JobRunner x = runner(l,r,c,b);
    Lease lease = x.begin("j", "a", 0, 10);
    x.finish("j", lease, "DONE", new FailureInjector() {
      @Override public void afterExternalEffect(String jobId, long token) {
        x.cancel(jobId);
      }
    });
    check("CANCELLED".equals(r.get("j")));
    check(r.token("j") == lease.token);
  }

  static void check(boolean x) {
    if (!x) throw new AssertionError();
  }
}'''
    (root/"FrontierLeaseFencingHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run([
        "javac","-d",str(outdir),
        *map(str,(root/"src").glob("*.java")),
        str(root/"FrontierLeaseFencingHiddenTest.java")
    ],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True)
        visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierLeaseFencingHiddenTest"],capture_output=True,text=True)
        hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("takeover_uses_monotonic_fencing_token",15,"TOKEN_PASS" in hidden_out)
    add("stale_or_wrong_generation_renew_is_rejected",10,"RENEW_PASS" in hidden_out)
    add("stale_worker_cannot_commit_or_emit_effect",20,"STALE_PASS" in hidden_out)
    add("same_generation_crash_retry_is_idempotent",15,"CRASH_SAME_PASS" in hidden_out)
    add("takeover_retry_reuses_business_idempotency_identity",15,"CRASH_TAKEOVER_PASS" in hidden_out)
    add("cancellation_wins_race_with_completion",15,"CANCEL_PASS" in hidden_out)


elif task == "frontier-incident-chain":
    state={}
    for line in text(".state").splitlines():
        if "=" in line:
            k,v=line.split("=",1)
            state[k.strip()]=v.strip()
    actions=[x.strip() for x in text(".actions").splitlines() if x.strip()]
    report=text("REPORT.txt").lower()

    def pos(prefix, start=0):
        for i,x in enumerate(actions[start:], start):
            if x == prefix or x.startswith(prefix+" "):
                return i
        return None

    config_fix=pos("replace-config")
    first_verify=pos("verify", (config_fix+1) if config_fix is not None else 0)
    consumer_fix=pos("replace-consumer", (first_verify+1) if first_verify is not None else 0)
    second_verify=pos("verify", (consumer_fix+1) if consumer_fix is not None else 0)
    invalidator_fix=pos("replace-invalidator", (second_verify+1) if second_verify is not None else 0)

    config_evidence=False
    if config_fix is not None:
        before=actions[:config_fix]
        config_evidence=("config api-b" in before or "logs api-b" in before) and "pods" in before

    fulfillment_evidence=False
    if first_verify is not None and consumer_fix is not None and consumer_fix > first_verify:
        between=actions[first_verify+1:consumer_fix]
        fulfillment_evidence=("queue" in between and "logs consumer-2" in between)

    cache_evidence=False
    if second_verify is not None and invalidator_fix is not None and invalidator_fix > second_verify:
        between=actions[second_verify+1:invalidator_fix]
        cache_evidence=("cache" in between and ("invalidators" in between or "logs invalidator-b" in between))

    dangerous=any(
        x=="restart-all" or x.startswith("scale ") or x=="reset-offset" or x=="flush-cache"
        for x in actions
    )

    add("targeted_config_repair",15,state.get("config_bad")=="0")
    add("verification_exposed_fulfillment_failure",10,state.get("fulfillment_seen")=="1")
    add("targeted_consumer_repair",15,state.get("consumer_bad")=="0")
    add("verification_exposed_cache_failure",10,state.get("cache_seen")=="1")
    add("targeted_invalidator_repair",15,state.get("invalidator_bad")=="0")
    add("config_evidence_before_mutation",5,config_evidence)
    add("fulfillment_evidence_before_mutation",5,fulfillment_evidence)
    add("cache_evidence_before_mutation",5,cache_evidence)
    add("avoided_broad_or_destructive_actions",5,not dangerous)
    add("final_end_to_end_verification",10,state.get("final_verified")=="1")
    report_ok=(
        ("config" in report and ("revision" in report or "payment_mode" in report))
        and ("consumer" in report and ("duplicate" in report or "dedup" in report or "contract" in report))
        and ("invalidator" in report and ("cache" in report or "stale" in report or "legacy" in report))
    )
    add("reported_all_failure_domains",5,report_ok)


elif task == "frontier-pagination":
    hidden = r'''import java.util.*;

public final class FrontierPaginationHiddenTest {
  public static void main(String[] args) {
    run("TIES", FrontierPaginationHiddenTest::tieBoundary);
    run("SNAPSHOT", FrontierPaginationHiddenTest::snapshotIsolation);
    run("LEGACY", FrontierPaginationHiddenTest::legacyCursor);
    run("TRAVERSE", FrontierPaginationHiddenTest::completeTraversal);
    run("INVALID", FrontierPaginationHiddenTest::invalidCursor);
  }

  interface Case { void run() throws Exception; }

  static void run(String name, Case c) {
    try { c.run(); System.out.println(name + "_PASS"); }
    catch (Throwable t) { System.out.println(name + "_FAIL:" + t); }
  }

  static void tieBoundary() {
    FeedStore store = new FeedStore();
    store.add(10, 300, "a");
    store.add(9, 200, "b");
    store.add(8, 200, "c");
    store.add(7, 200, "d");
    store.add(6, 100, "e");
    FeedService service = new FeedService(store, new CursorCodec());

    Page p1 = service.page(null, 2);
    Page p2 = service.page(p1.nextToken, 2);
    check(ids(p1).equals(List.of(10L, 9L)));
    check(ids(p2).equals(List.of(8L, 7L)));
  }

  static void snapshotIsolation() {
    FeedStore store = new FeedStore();
    store.add(5, 500, "a");
    store.add(4, 400, "b");
    store.add(3, 300, "c");
    store.add(2, 200, "d");
    store.add(1, 100, "e");
    FeedService service = new FeedService(store, new CursorCodec());

    Page p1 = service.page(null, 2);
    store.add(99, 350, "late");
    store.add(100, 50, "late-low");
    Page p2 = service.page(p1.nextToken, 2);
    Page p3 = service.page(p2.nextToken, 2);

    List<Long> seen = new ArrayList<>();
    seen.addAll(ids(p1)); seen.addAll(ids(p2)); seen.addAll(ids(p3));
    check(seen.equals(List.of(5L,4L,3L,2L,1L)));
    check(!seen.contains(99L) && !seen.contains(100L));
  }

  static void legacyCursor() {
    FeedStore store = new FeedStore();
    store.add(5, 500, "a");
    store.add(4, 400, "b");
    store.add(3, 300, "c");
    store.add(2, 200, "d");
    store.add(1, 100, "e");
    FeedService service = new FeedService(store, new CursorCodec());

    Page p = service.page("v1:300", 10);
    check(ids(p).equals(List.of(2L,1L)));
    check(p.nextToken == null);
  }

  static void completeTraversal() {
    FeedStore store = new FeedStore();
    store.add(12, 400, "a");
    store.add(11, 400, "b");
    store.add(10, 400, "c");
    store.add(9, 300, "d");
    store.add(8, 300, "e");
    store.add(7, 200, "f");
    store.add(6, 100, "g");
    FeedService service = new FeedService(store, new CursorCodec());

    List<Long> got = new ArrayList<>();
    String token = null;
    int pages = 0;
    do {
      Page p = service.page(token, 2);
      got.addAll(ids(p));
      token = p.nextToken;
      pages++;
      check(pages < 10);
    } while (token != null);

    check(got.equals(List.of(12L,11L,10L,9L,8L,7L,6L)));
    check(new HashSet<>(got).size() == got.size());
  }

  static void invalidCursor() {
    FeedStore store = new FeedStore();
    store.add(1, 1, "a");
    FeedService service = new FeedService(store, new CursorCodec());
    expectBad(() -> service.page("v2:not-a-number:1:1", 10));
    expectBad(() -> service.page("garbage", 10));
  }

  static List<Long> ids(Page p) {
    List<Long> out = new ArrayList<>();
    for (FeedItem x : p.items) out.add(x.id);
    return out;
  }

  interface Bad { void run(); }
  static void expectBad(Bad b) {
    boolean ok=false;
    try { b.run(); } catch (IllegalArgumentException e) { ok=true; }
    check(ok);
  }

  static void check(boolean x) {
    if (!x) throw new AssertionError();
  }
}'''
    (root/"FrontierPaginationHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run([
        "javac","-d",str(outdir),
        *map(str,(root/"src").glob("*.java")),
        str(root/"FrontierPaginationHiddenTest.java")
    ],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; probe=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True)
        visible=vr.returncode==0
        pr=subprocess.run(["java","-cp",str(outdir),"PaginationProbe"],capture_output=True,text=True)
        probe=pr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierPaginationHiddenTest"],capture_output=True,text=True)
        hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("repository_diagnostic_probe",10,probe)
    add("stable_total_order_across_timestamp_ties",20,"TIES_PASS" in hidden_out)
    add("cursor_pins_snapshot_across_writes",25,"SNAPSHOT_PASS" in hidden_out)
    add("legacy_cursor_remains_accepted",15,"LEGACY_PASS" in hidden_out)
    add("complete_duplicate_free_traversal",15,"TRAVERSE_PASS" in hidden_out)
    add("invalid_cursor_rejected",5,"INVALID_PASS" in hidden_out)


elif task == "frontier-review-deep":
    raw=text("FINDINGS.json")
    try:
        data=json.loads(raw)
        findings=data.get("findings",[]) if isinstance(data,dict) else []
        valid=isinstance(findings,list) and isinstance(data.get("verdict"),str)
    except Exception:
        data={}
        findings=[]
        valid=False

    add("valid_findings_json",5,valid)

    expected={
        ("PriceService.java","ignored_write_result"):15,
        ("PriceService.java","transaction_visibility"):15,
        ("AuditWorker.java","payload_snapshot"):10,
        ("AuditWorker.java","retry_idempotency"):10,
        ("WebhookService.java","business_identity_scope"):20,
        ("WebhookService.java","external_effect_recovery"):10,
        ("ReservationMover.java","lock_order"):10,
    }

    reported=set()
    if valid:
        for item in findings:
            if not isinstance(item,dict):
                continue
            file=str(item.get("file","")).strip().split("/")[-1]
            failure=str(item.get("failure_class","")).strip().lower()
            if file and failure:
                reported.add((file,failure))

    for (file,failure),points in expected.items():
        add(f"finding_{file}_{failure}",points,(file,failure) in reported)

    # Plausible additional blocking domains may be reported without earning
    # hidden-checklist credit. They must not be mislabeled as false positives.
    allowed_optional={
        ("WebhookService.java","lost_update"),
    }
    extras=sorted(reported-set(expected)-allowed_optional)
    if extras:
        penalty=min(15,5*len(extras))
        score-=penalty
        checks["false_positive_penalty"]={
            "points":-penalty,
            "passed":False,
            "reported":[{"file":f,"failure_class":c} for f,c in extras],
        }

    verdict=str(data.get("verdict","")).strip().upper() if valid else ""
    add("requests_changes",5,verdict=="REQUEST_CHANGES")

elif task == "frontier-key-rotation":
    hidden = r'''public final class FrontierKeyRotationHiddenTest {
  public static void main(String[] args) {
    run("LEGACY", FrontierKeyRotationHiddenTest::legacyOverlap);
    run("KEYED_OLD", FrontierKeyRotationHiddenTest::keyedPreviousStillValid);
    run("UNKNOWN", FrontierKeyRotationHiddenTest::unknownKidRejected);
    run("ISSUER", FrontierKeyRotationHiddenTest::issuerScopedSameKid);
    run("REMOVED", FrontierKeyRotationHiddenTest::removedKeyInvalidatesCache);
    run("REPLACE", FrontierKeyRotationHiddenTest::sameKidReplacementInvalidatesCache);
    run("ACTIVE", FrontierKeyRotationHiddenTest::activeIssueAndVerify);
  }

  interface Case { void run(); }

  static void run(String name, Case c) {
    try { c.run(); System.out.println(name + "_PASS"); }
    catch (Throwable t) { System.out.println(name + "_FAIL:" + t); }
  }

  static void legacyOverlap() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","old","s-old",false);
    r.addKey("a","new","s-new",true);
    TokenCodec c=new TokenCodec();
    TokenVerifier v=new TokenVerifier(r,new KeyCache(),c);
    check(v.verify(c.encode("a",null,"u","s-old")));
    check(v.verify(c.encode("a",null,"u","s-new")));
  }

  static void keyedPreviousStillValid() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","old","s-old",false);
    r.addKey("a","new","s-new",true);
    TokenCodec c=new TokenCodec();
    TokenVerifier v=new TokenVerifier(r,new KeyCache(),c);
    check(v.verify(c.encode("a","old","u","s-old")));
  }

  static void unknownKidRejected() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","new","s-new",true);
    TokenCodec c=new TokenCodec();
    TokenVerifier v=new TokenVerifier(r,new KeyCache(),c);
    check(!v.verify(c.encode("a","missing","u","s-new")));
  }

  static void issuerScopedSameKid() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","shared","sa",true);
    r.addKey("b","shared","sb",true);
    TokenCodec c=new TokenCodec(); KeyCache cache=new KeyCache();
    TokenVerifier v=new TokenVerifier(r,cache,c);
    check(v.verify(c.encode("a","shared","alice","sa")));
    check(v.verify(c.encode("b","shared","bob","sb")));
    check(!v.verify(c.encode("b","shared","bob","sa")));
  }

  static void removedKeyInvalidatesCache() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","old","s-old",false);
    r.addKey("a","new","s-new",true);
    TokenCodec c=new TokenCodec(); KeyCache cache=new KeyCache();
    TokenVerifier v=new TokenVerifier(r,cache,c);
    String old=c.encode("a","old","u","s-old");
    check(v.verify(old));
    r.removeKey("a","old");
    check(!v.verify(old));
    check(!v.verify(c.encode("a",null,"u","s-old")));
  }

  static void sameKidReplacementInvalidatesCache() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","rotating","s1",true);
    TokenCodec c=new TokenCodec(); KeyCache cache=new KeyCache();
    TokenVerifier v=new TokenVerifier(r,cache,c);
    check(v.verify(c.encode("a","rotating","u","s1")));
    r.addKey("a","rotating","s2",true);
    check(!v.verify(c.encode("a","rotating","u","s1")));
    check(v.verify(c.encode("a","rotating","u","s2")));
  }

  static void activeIssueAndVerify() {
    KeyRegistry r=new KeyRegistry();
    r.addKey("a","old","s-old",false);
    r.addKey("a","new","s-new",true);
    TokenCodec c=new TokenCodec();
    TokenSigner signer=new TokenSigner(r,c);
    TokenVerifier v=new TokenVerifier(r,new KeyCache(),c);
    String token=signer.issue("a","u");
    check(token.contains(";new;"));
    check(v.verify(token));
  }

  static void check(boolean x) {
    if(!x) throw new AssertionError();
  }
}'''
    (root/"FrontierKeyRotationHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run([
        "javac","-d",str(outdir),
        *map(str,(root/"src").glob("*.java")),
        str(root/"FrontierKeyRotationHiddenTest.java")
    ],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; rollout=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True)
        visible=vr.returncode==0
        rr=subprocess.run(["bash","run_rollout_checks.sh"],cwd=root,capture_output=True,text=True,timeout=30)
        rollout=rr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"FrontierKeyRotationHiddenTest"],capture_output=True,text=True)
        hidden_out=hr.stdout+hr.stderr
    add("visible_regression",5,visible)
    add("repository_rollout_probe",10,rollout)
    add("legacy_no_kid_uses_retained_overlap_keys",15,"LEGACY_PASS" in hidden_out)
    add("previous_keyed_session_remains_valid_during_overlap",10,"KEYED_OLD_PASS" in hidden_out)
    add("unknown_kid_is_rejected_without_fallback",15,"UNKNOWN_PASS" in hidden_out)
    add("key_cache_is_scoped_by_issuer",15,"ISSUER_PASS" in hidden_out)
    add("removed_key_invalidates_cached_verification",15,"REMOVED_PASS" in hidden_out)
    add("same_kid_replacement_observes_registry_revision",15,"REPLACE_PASS" in hidden_out)
    add("active_signing_path_regression",10,"ACTIVE_PASS" in hidden_out)

elif task == "staged-identity-evolution":
    hidden = r'''import java.util.*;
import java.util.concurrent.*;

public final class StagedIdentityEvolutionHiddenTest {
  public static void main(String[] args) {
    run("LEGACY_STABLE", StagedIdentityEvolutionHiddenTest::legacyStable);
    run("CONCURRENT", StagedIdentityEvolutionHiddenTest::concurrentAssignment);
    run("NO_ROTATE", StagedIdentityEvolutionHiddenTest::assignedKeyDoesNotRotate);
    run("V1_PRESERVE", StagedIdentityEvolutionHiddenTest::v1PreservesKey);
    run("REST", StagedIdentityEvolutionHiddenTest::restContract);
    run("JWT", StagedIdentityEvolutionHiddenTest::jwtContract);
    run("KAFKA", StagedIdentityEvolutionHiddenTest::kafkaContract);
    run("CACHE_FALLBACK", StagedIdentityEvolutionHiddenTest::cacheFallback);
    run("CACHE_PREFER", StagedIdentityEvolutionHiddenTest::cachePreference);
    run("CACHE_INVALIDATE", StagedIdentityEvolutionHiddenTest::cacheInvalidation);
  }

  interface Case { void run() throws Exception; }

  static void run(String name, Case c) {
    try { c.run(); System.out.println(name + "_PASS"); }
    catch(Throwable t) { System.out.println(name + "_FAIL:" + t); }
  }

  static void legacyStable() {
    CustomerStore s=new CustomerStore();
    V1CustomerService v1=new V1CustomerService(s);
    IdentityService ids=new IdentityService(s);
    Customer c=v1.write(41L,"Legacy");
    String a=ids.customerKey(41L), b=ids.customerKey(41L);
    check(a!=null && !a.isBlank());
    check(a.equals(b));
    check(a.equals(c.customerKey));
  }

  static void concurrentAssignment() throws Exception {
    CustomerStore s=new CustomerStore();
    new V1CustomerService(s).write(42L,"Concurrent");
    IdentityService ids=new IdentityService(s);
    int n=10;
    CountDownLatch ready=new CountDownLatch(n), go=new CountDownLatch(1);
    Set<String> seen=Collections.synchronizedSet(new HashSet<>());
    List<Thread> threads=new ArrayList<>();
    for(int i=0;i<n;i++){
      Thread t=new Thread(()->{
        try { ready.countDown(); go.await(); seen.add(ids.customerKey(42L)); }
        catch(InterruptedException e){ throw new RuntimeException(e); }
      });
      threads.add(t); t.start();
    }
    ready.await(); go.countDown();
    for(Thread t:threads)t.join();
    check(seen.size()==1);
    check(seen.iterator().next().equals(s.get(42L).customerKey));
  }

  static void assignedKeyDoesNotRotate() {
    CustomerStore s=new CustomerStore();
    IdentityService ids=new IdentityService(s);
    V2CustomerService v2=new V2CustomerService(s,ids);
    Customer a=v2.write(7L,"ck-original","A");
    Customer b=v2.write(7L,"ck-other","B");
    check("ck-original".equals(a.customerKey));
    check("ck-original".equals(b.customerKey));
  }

  static void v1PreservesKey() {
    CustomerStore s=new CustomerStore();
    IdentityService ids=new IdentityService(s);
    V1CustomerService v1=new V1CustomerService(s);
    V2CustomerService v2=new V2CustomerService(s,ids);
    Customer c=v2.write(8L,"ck-8","A");
    v1.write(8L,"B");
    check("ck-8".equals(c.customerKey));
    check("B".equals(c.name));
  }

  static Customer contractCustomer() {
    Customer c=new Customer(9L,"Contract");
    c.customerKey="ck-9";
    return c;
  }

  static void restContract() {
    Customer c=contractCustomer();
    String x=new RestContract().encode(c);
    check(x.contains("customer_id") && x.contains("9"));
    check(x.contains("customer_key") && x.contains("ck-9"));
  }

  static void jwtContract() {
    Customer c=contractCustomer();
    String x=new JwtContract().claims(c);
    check(x.contains("customer_id") && x.contains("9"));
    check(x.contains("customer_key") && x.contains("ck-9"));
  }

  static void kafkaContract() {
    Customer c=contractCustomer();
    String x=new KafkaContract().event(c);
    check(x.contains("customer_id") && x.contains("9"));
    check(x.contains("customer_key") && x.contains("ck-9"));
  }

  static void cacheFallback() {
    CustomerCache c=new CustomerCache();
    c.putLegacy(12L,"old");
    check("old".equals(c.getCompatible(12L,"ck-12")));
  }

  static void cachePreference() {
    CustomerCache c=new CustomerCache();
    c.putLegacy(12L,"old");
    c.putV2("ck-12","new");
    check("new".equals(c.getCompatible(12L,"ck-12")));
  }

  static void cacheInvalidation() {
    CustomerCache c=new CustomerCache();
    c.putLegacy(12L,"old");
    c.putV2("ck-12","new");
    c.invalidateLegacy(12L,"ck-12");
    check(c.getCompatible(12L,"ck-12")==null);
    check(c.size()==0);
  }

  static void check(boolean x) {
    if(!x) throw new AssertionError();
  }
}'''
    (root/"StagedIdentityEvolutionHiddenTest.java").write_text(hidden)
    outdir=root/"hidden-out"; outdir.mkdir(exist_ok=True)
    cp=subprocess.run([
        "javac","-d",str(outdir),
        *map(str,(root/"src").glob("*.java")),
        str(root/"StagedIdentityEvolutionHiddenTest.java")
    ],capture_output=True,text=True)
    add("compiles",5,cp.returncode==0)
    visible=False; hidden_out=""
    if cp.returncode==0:
        vr=subprocess.run(["java","-cp",str(outdir),"VisibleTest"],capture_output=True,text=True)
        visible=vr.returncode==0
        hr=subprocess.run(["java","-cp",str(outdir),"StagedIdentityEvolutionHiddenTest"],capture_output=True,text=True)
        hidden_out=hr.stdout+hr.stderr

    add("visible_regression",5,visible)
    add("stage1_legacy_key_stable_and_persisted",15,"LEGACY_STABLE_PASS" in hidden_out)
    add("stage1_concurrent_assignment_single_key",10,"CONCURRENT_PASS" in hidden_out)
    add("stage1_assigned_key_never_rotates",10,"NO_ROTATE_PASS" in hidden_out)
    add("stage1_v1_update_preserves_key",5,"V1_PRESERVE_PASS" in hidden_out)
    add("stage2_rest_additive_contract",8,"REST_PASS" in hidden_out)
    add("stage2_jwt_additive_contract",7,"JWT_PASS" in hidden_out)
    add("stage2_kafka_additive_contract",10,"KAFKA_PASS" in hidden_out)
    add("stage3_cache_legacy_fallback",10,"CACHE_FALLBACK_PASS" in hidden_out)
    add("stage3_cache_v2_preference",5,"CACHE_PREFER_PASS" in hidden_out)
    add("stage3_dual_namespace_invalidation",10,"CACHE_INVALIDATE_PASS" in hidden_out)


elif task == "frontier-build-cache":
    visible=False
    try:
        vr=subprocess.run(["bash","run_visible_tests.sh"],cwd=root,capture_output=True,text=True,timeout=30)
        visible=vr.returncode==0
    except Exception:
        visible=False
    add("visible_regression",10,visible)

    verifier=Path("benchmarks/frontier-build-cache/blackbox_validate.py").resolve()
    blackbox=""
    try:
        br=subprocess.run([sys.executable,str(verifier),str(root)],capture_output=True,text=True,timeout=60)
        blackbox=br.stdout+br.stderr
    except Exception as e:
        blackbox=str(e)

    add("direct_source_change_rebuilds",10,"PASS direct_change" in blackbox)
    add("transitive_dependency_change_invalidates_downstream",30,"PASS transitive_change" in blackbox)
    add("failed_rebuild_does_not_poison_cache",30,"PASS retry_after_compile_failure" in blackbox)
    add("unrelated_change_does_not_overbuild",10,"PASS unrelated_change" in blackbox)
    add("dependency_cycle_is_rejected",10,"PASS cycle_rejected" in blackbox)


elif task == "frontier-import-resume":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-import-resume.py"
    proc=subprocess.run(
        [sys.executable,str(validator),str(root),"--json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        data=json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        data={"compiles":False,"cases":{}}
    cases=data.get("cases",{}) if isinstance(data,dict) else {}

    add("compiles",5,bool(data.get("compiles")))

    visible=False
    try:
        vr=subprocess.run(["bash","run_visible_tests.sh"],cwd=root,capture_output=True,text=True,timeout=30)
        visible=vr.returncode==0
    except Exception:
        visible=False
    add("visible_regression",5,visible)

    add("crash_retry_exactly_once_external_effect",20,bool(cases.get("CRASH")))
    add("snapshot_pinned_before_external_effect",30,bool(cases.get("SNAPSHOT")))
    add("stable_ordering_across_ties",15,bool(cases.get("TIES")))
    add("concurrent_resume_converges",25,bool(cases.get("CONCURRENT")))


elif task == "frontier-plan-runtime":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-plan-runtime.py"
    result={}
    try:
        vr=subprocess.run(
            ["python",str(validator),str(root),"--json"],
            capture_output=True,text=True,timeout=30
        )
        result=json.loads(vr.stdout)
    except Exception:
        result={}
    d=result.get("domains",{})
    add("valid_decision_json",5,bool(d.get("syntax")))
    add("known_unique_actions",5,bool(d.get("known_unique_actions")))
    add("online_non_disruptive_rollout",10,bool(d.get("online_safe")))
    add("mixed_version_persistence_compatibility",15,bool(d.get("persistence_compatibility")))
    add("live_backfill_race_safety",15,bool(d.get("backfill_race_safety")))
    add("consumer_before_producer_event_compatibility",10,bool(d.get("event_compatibility")))
    add("mixed_version_cache_compatibility",10,bool(d.get("cache_compatibility")))
    add("cutover_only_after_all_readiness_gates",10,bool(d.get("cutover_gate")))
    add("rollback_window_before_irreversible_cleanup",15,bool(d.get("rollback_safety")))
    add("minimal_sufficient_action_set",5,bool(d.get("minimal_sufficient")))


elif task == "frontier-deep-fix":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-deep-fix.py"
    result={}
    try:
        vr=subprocess.run(
            ["python",str(validator),str(root),"--json"],
            capture_output=True,text=True,timeout=30
        )
        result=json.loads(vr.stdout)
    except Exception:
        result={}
    cases=result.get("cases",{})
    add("compiles",5,bool(result.get("compiles")))
    add("visible_regression",5,bool(result.get("visible")))
    add("optimistic_conflict_blocks_followup",10,bool(cases.get("OPTIMISTIC")))
    add("cache_and_audit_after_commit",15,bool(cases.get("TX")))
    add("audit_payload_snapshots_accepted_version",10,bool(cases.get("AUDIT_SNAPSHOT")))
    add("audit_retry_uses_stable_business_key",10,bool(cases.get("AUDIT_IDEMP")))
    add("fulfillment_identity_is_business_scoped",15,bool(cases.get("BUSINESS_ID")))
    add("post_side_effect_crash_retry_converges",20,bool(cases.get("CRASH_RETRY")))
    add("canonical_pair_lock_order",10,bool(cases.get("LOCK_ORDER")))


elif task == "frontier-runtime-diagnosis":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-runtime-diagnosis.py"
    result={}
    try:
        vr=subprocess.run(
            ["python",str(validator),str(root),"--json"],
            capture_output=True,text=True,timeout=30
        )
        result=json.loads(vr.stdout)
    except Exception:
        result={}

    runner={}
    try:
        runner=json.loads((root/"light-agent-result.json").read_text())
    except Exception:
        runner={}
    queries=[str(x).strip().lower() for x in runner.get("probe_queries",[])]

    config_evidence=(
        "pods" in queries
        and ("config api-b" in queries or "logs api-b" in queries or "experiment normal api-b" in queries)
    )
    retry_evidence=(
        "experiment timeout api-a" in queries
        or (
            "queue" in queries
            and "experiment normal api-a" in queries
            and "experiment timeout api-b" in queries
        )
    )

    add("valid_repair_json",5,bool(result.get("syntax")))
    add("identified_api_config_drift",15,bool(result.get("config_root")))
    add("identified_retry_idempotency_scope",20,bool(result.get("idempotency_root")))
    add("targeted_config_repair",15,bool(result.get("config_action")))
    add("business_scoped_idempotency_repair",20,bool(result.get("idempotency_action")))
    add("minimal_no_unrelated_repairs",10,bool(result.get("minimal")))
    add("collected_config_causal_evidence",5,config_evidence)
    add("isolated_retry_failure_on_healthy_pod",10,retry_evidence)


elif task == "frontier-runtime-diagnosis-v2":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-runtime-diagnosis-v2.py"
    result={}
    try:
        vr=subprocess.run(
            ["python",str(validator),str(root),"--json"],
            capture_output=True,text=True,timeout=30
        )
        result=json.loads(vr.stdout)
    except Exception:
        result={}

    runner={}
    try:
        runner=json.loads((root/"light-agent-result.json").read_text())
    except Exception:
        runner={}
    queries=[str(x).strip().lower() for x in runner.get("probe_executed_queries", runner.get("probe_queries",[]))]

    config_evidence=any(
        "api-b" in q and any(k in q for k in ("config","configuration","rendered","log","500"))
        for q in queries
    )
    retry_evidence=any(
        "api-a" in q and any(k in q for k in ("timeout","retry","replay","experiment","inject"))
        for q in queries
    )

    add("valid_repair_json",5,bool(result.get("syntax")))
    add("identified_api_config_drift",15,bool(result.get("config_root")))
    add("identified_retry_idempotency_scope",20,bool(result.get("retry_root")))
    add("targeted_config_repair",15,bool(result.get("config_action")))
    add("business_scoped_idempotency_repair",20,bool(result.get("retry_action")))
    add("minimal_no_unrelated_repairs",10,bool(result.get("minimal")))
    add("collected_pod_specific_config_evidence",5,config_evidence)
    add("isolated_retry_failure_on_healthy_pod",10,retry_evidence)

elif task == "frontier-dynamic-diagnosis":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-dynamic-diagnosis.py"
    result={}
    try:
        vr=subprocess.run(
            ["python",str(validator),str(root),"--json"],
            capture_output=True,text=True,timeout=30
        )
        result=json.loads(vr.stdout)
    except Exception:
        result={}

    diagnosis={}
    try:
        diagnosis=json.loads((root/"DIAGNOSIS.json").read_text())
    except Exception:
        diagnosis={}
    roots=set(x for x in diagnosis.get("root_causes",[]) if isinstance(x,str))
    actions=set(x for x in diagnosis.get("actions",[]) if isinstance(x,str))
    variant=int(result.get("variant",1))

    expected={
        1:{
            "roots":["api_config_drift","retry_idempotency_scope"],
            "actions":["replace_drifted_api","fix_business_idempotency"],
        },
        2:{
            "roots":["capacity_shortage","stale_consumer_contract"],
            "actions":["scale_checkout_api","replace_incompatible_consumer"],
        },
        3:{
            "roots":["cache_invalidator_gap","replica_read_lag"],
            "actions":["repair_dual_invalidation","route_strict_reads_primary"],
        },
    }[variant]

    runner={}
    try:
        runner=json.loads((root/"light-agent-result.json").read_text())
    except Exception:
        runner={}
    queries=[str(x).strip().lower() for x in runner.get("probe_executed_queries",runner.get("probe_queries",[]))]

    evidence={
        1:[
            ("http_config_causality",
             "slice http-errors by pod" in queries and
             ("component api-b" in queries or "experiment retry api-b" in queries)),
            ("provider_retry_causality",
             "slice duplicate-effects by boundary" in queries and
             "experiment retry api-a" in queries),
        ],
        2:[
            ("capacity_causality",
             "slice http-errors by pod" in queries and "capacity" in queries),
            ("consumer_replay_causality",
             "slice duplicate-effects by boundary" in queries and
             ("component consumer-2" in queries or "queue" in queries)),
        ],
        3:[
            ("cache_alias_causality",
             "slice stale-reads by path" in queries and
             ("component invalidator-b" in queries or "cache" in queries)),
            ("replica_lag_causality",
             "experiment strict-read primary" in queries and
             "experiment strict-read replica" in queries),
        ],
    }[variant]

    add("valid_diagnosis_json",5,bool(result.get("syntax")))
    add("known_unique_ids",5,bool(result.get("known_unique")))
    add("root_cause_a",15,expected["roots"][0] in roots)
    add("root_cause_b",15,expected["roots"][1] in roots)
    add("repair_action_a",15,expected["actions"][0] in actions)
    add("repair_action_b",15,expected["actions"][1] in actions)
    add("minimal_no_false_positive_repairs",10,bool(result.get("minimal")))
    add("causal_evidence_a",10,bool(evidence[0][1]))
    add("causal_evidence_b",10,bool(evidence[1][1]))


elif task == "frontier-fullstack-autosave":
    validator=Path(__file__).resolve().parent/"validators"/"frontier-fullstack-autosave.py"
    result={}
    try:
        vr=subprocess.run(
            ["python",str(validator),str(root),"--json"],
            capture_output=True,text=True,timeout=30
        )
        result=json.loads(vr.stdout)
    except Exception:
        result={}

    runner={}
    try:
        runner=json.loads((root/"light-agent-result.json").read_text())
    except Exception:
        runner={}
    queries=[str(x).strip().lower() for x in runner.get("probe_executed_queries", runner.get("probe_queries",[]))]
    runtime_evidence=(
        any(("timeout" in q or "retry" in q) for q in queries)
        and any(("conflict" in q or "409" in q or "concurrent" in q) for q in queries)
    )

    add("syntax_valid",5,bool(result.get("syntax")))
    add("visible_regression",5,bool(result.get("visible")))
    add("timeout_retry_converges_once",25,bool(result.get("timeout")))
    add("version_conflict_does_not_overwrite",20,bool(result.get("conflict")))
    add("local_editor_state_waits_for_confirmed_result",10,bool(result.get("state")))
    add("backend_same_operation_recovers_after_commit_timeout",20,bool(result.get("backend_retry")))
    add("separate_user_edits_remain_distinct",10,bool(result.get("separate")))
    add("investigated_both_runtime_failure_domains",5,runtime_evidence)

else:
    raise SystemExit(f"unknown task {task}")

score=max(0,min(100,score))
result={"task":task,"score":score,"checks":checks}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
