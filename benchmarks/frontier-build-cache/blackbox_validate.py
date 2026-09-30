#!/usr/bin/env python3
import subprocess, sys, tempfile
from pathlib import Path

root=Path(sys.argv[1]).resolve()
hidden=r"""
import java.util.*;

public final class BlackBoxBuildCacheTest {
  public static void main(String[] args) {
    int failures=0;
    failures += run("direct_change", BlackBoxBuildCacheTest::directChange);
    failures += run("transitive_change", BlackBoxBuildCacheTest::transitiveChange);
    failures += run("retry_after_compile_failure", BlackBoxBuildCacheTest::retryAfterCompileFailure);
    failures += run("unrelated_change", BlackBoxBuildCacheTest::unrelatedChange);
    failures += run("cycle_rejected", BlackBoxBuildCacheTest::cycleRejected);
    if (failures>0) System.exit(1);
  }

  interface Case { void run(); }

  static int run(String name, Case c) {
    try {
      c.run();
      System.out.println("PASS " + name);
      return 0;
    } catch (Throwable t) {
      System.out.println("FAIL " + name + ": " + t.getMessage());
      return 1;
    }
  }

  static void directChange() {
    Workspace ws=new Workspace(); ws.add("app","v1");
    Compiler c=new Compiler(); IncrementalBuilder b=new IncrementalBuilder(ws,new BuildCache(),c);
    b.build("app"); ws.updateSource("app","v2");
    Artifact a=b.build("app");
    check(a.output().contains("v2"),"direct edit returned stale artifact");
    check(c.buildCount("app")==2,"direct edit did not rebuild exactly once");
  }

  static void transitiveChange() {
    Workspace ws=new Workspace();
    ws.add("core","core-v1");
    ws.add("lib","lib-v1","core");
    ws.add("app","app-v1","lib");
    Compiler c=new Compiler(); IncrementalBuilder b=new IncrementalBuilder(ws,new BuildCache(),c);
    Artifact first=b.build("app");
    ws.updateSource("core","core-v2");
    Artifact second=b.build("app");
    check(!first.output().equals(second.output()),"app artifact did not change after transitive dependency changed");
    check(second.output().contains("core-v2"),"app artifact remained stale after transitive dependency changed");
  }

  static void retryAfterCompileFailure() {
    Workspace ws=new Workspace(); ws.add("app","v1");
    Compiler c=new Compiler(); IncrementalBuilder b=new IncrementalBuilder(ws,new BuildCache(),c);
    Artifact old=b.build("app");
    ws.updateSource("app","v2");
    c.failNext("app");
    boolean failed=false;
    try { b.build("app"); } catch (IllegalStateException expected) { failed=true; }
    check(failed,"injected compile failure did not surface");
    Artifact retried=b.build("app");
    check(retried!=null,"retry returned no artifact");
    check(!old.output().equals(retried.output()),"retry reused artifact from before failed rebuild");
    check(retried.output().contains("v2"),"retry did not publish rebuilt v2 artifact");
  }

  static void unrelatedChange() {
    Workspace ws=new Workspace();
    ws.add("core","core-v1");
    ws.add("app","app-v1","core");
    ws.add("tools","tools-v1");
    Compiler c=new Compiler(); IncrementalBuilder b=new IncrementalBuilder(ws,new BuildCache(),c);
    Artifact first=b.build("app");
    int appBuilds=c.buildCount("app"), coreBuilds=c.buildCount("core");
    ws.updateSource("tools","tools-v2");
    Artifact second=b.build("app");
    check(first.output().equals(second.output()),"unrelated change altered app artifact");
    check(c.buildCount("app")==appBuilds && c.buildCount("core")==coreBuilds,
          "unrelated module change caused unnecessary rebuild");
  }

  static void cycleRejected() {
    Workspace ws=new Workspace();
    ws.add("a","a","b");
    ws.add("b","b","a");
    IncrementalBuilder builder=new IncrementalBuilder(ws,new BuildCache(),new Compiler());
    boolean bad=false;
    try { builder.build("a"); } catch (IllegalArgumentException expected) { bad=true; }
    check(bad,"dependency cycle was not rejected");
  }

  static void check(boolean ok,String message) {
    if(!ok) throw new AssertionError(message);
  }
}
"""

with tempfile.TemporaryDirectory(prefix="bb-build-cache-") as td:
    td=Path(td)
    src=td/"BlackBoxBuildCacheTest.java"
    src.write_text(hidden)
    out=td/"out"; out.mkdir()
    java_files=[str(p) for p in (root/"src").glob("*.java")]
    cp=subprocess.run(["javac","-d",str(out),*java_files,str(src)],capture_output=True,text=True)
    if cp.returncode:
        print("FAIL compile: workspace does not compile with black-box checks")
        print(cp.stderr[-2000:])
        raise SystemExit(1)
    run=subprocess.run(["java","-cp",str(out),"BlackBoxBuildCacheTest"],capture_output=True,text=True)
    print(run.stdout,end="")
    if run.stderr:
        print(run.stderr[-2000:],file=sys.stderr)
    raise SystemExit(run.returncode)
