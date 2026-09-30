#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
json_mode = "--json" in sys.argv[2:]

hidden = r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public final class FrontierImportResumeHiddenTest {
  public static void main(String[] args) {
    run("CRASH", FrontierImportResumeHiddenTest::crashRetry);
    run("SNAPSHOT", FrontierImportResumeHiddenTest::snapshotPinnedBeforeEffects);
    run("TIES", FrontierImportResumeHiddenTest::orderingTies);
    run("CONCURRENT", FrontierImportResumeHiddenTest::concurrentResume);
  }

  interface Case { void run() throws Exception; }

  static void run(String name, Case c) {
    try { c.run(); System.out.println(name + "_PASS"); }
    catch (Throwable t) { System.out.println(name + "_FAIL:" + t); }
  }

  static ImportWorker worker(ImportSource source, CheckpointStore checkpoints, CustomerApi api) {
    return new ImportWorker(source, checkpoints, api);
  }

  static void seedBasic(ImportSource source) {
    source.add(3L, 300L, "c");
    source.add(2L, 200L, "b");
    source.add(1L, 100L, "a");
  }

  static void crashRetry() {
    ImportSource source = new ImportSource();
    seedBasic(source);
    CheckpointStore checkpoints = new CheckpointStore();
    CustomerApi api = new CustomerApi();
    ImportWorker worker = worker(source, checkpoints, api);
    AtomicBoolean once = new AtomicBoolean(true);

    try {
      worker.run("job-crash", rowId -> {
        if (once.getAndSet(false)) throw new RuntimeException("crash-after-upsert");
      });
    } catch (RuntimeException expected) {}

    worker.run("job-crash", FailureInjector.none());
    check(api.effectCount() == 3);
    check(api.hasRow(1L) && api.hasRow(2L) && api.hasRow(3L));
  }

  static void snapshotPinnedBeforeEffects() {
    ImportSource source = new ImportSource();
    seedBasic(source);
    CheckpointStore checkpoints = new CheckpointStore();
    CustomerApi api = new CustomerApi();
    ImportWorker worker = worker(source, checkpoints, api);
    AtomicBoolean once = new AtomicBoolean(true);

    try {
      worker.run("job-snapshot", rowId -> {
        if (once.getAndSet(false)) throw new RuntimeException("crash-before-progress-save");
      });
    } catch (RuntimeException expected) {}

    source.add(99L, 250L, "late");
    worker.run("job-snapshot", FailureInjector.none());

    check(api.effectCount() == 3);
    check(api.hasRow(1L) && api.hasRow(2L) && api.hasRow(3L));
    check(!api.hasRow(99L));
  }

  static void orderingTies() {
    ImportSource source = new ImportSource();
    source.add(10L, 300L, "a");
    source.add(9L, 200L, "b");
    source.add(8L, 200L, "c");
    source.add(7L, 200L, "d");
    source.add(6L, 100L, "e");

    CheckpointStore checkpoints = new CheckpointStore();
    CustomerApi api = new CustomerApi();
    worker(source, checkpoints, api).run("job-ties", FailureInjector.none());

    check(api.effectCount() == 5);
    check(api.hasRow(10L) && api.hasRow(9L) && api.hasRow(8L) && api.hasRow(7L) && api.hasRow(6L));
  }

  static void concurrentResume() throws Exception {
    ImportSource source = new ImportSource();
    for (long i = 1; i <= 6; i++) source.add(i, 700L - i * 10L, "v" + i);

    CheckpointStore checkpoints = new CheckpointStore();
    CustomerApi api = new CustomerApi();
    ImportWorker worker = worker(source, checkpoints, api);

    CountDownLatch ready = new CountDownLatch(2);
    CountDownLatch go = new CountDownLatch(1);
    List<Throwable> failures = Collections.synchronizedList(new ArrayList<>());

    Runnable run = () -> {
      try {
        ready.countDown();
        go.await();
        worker.run("job-concurrent", FailureInjector.none());
      } catch (Throwable t) {
        failures.add(t);
      }
    };

    Thread a = new Thread(run);
    Thread b = new Thread(run);
    a.start(); b.start();
    ready.await(); go.countDown();
    a.join(); b.join();

    check(failures.isEmpty());
    check(api.effectCount() == 6);
    for (long i = 1; i <= 6; i++) check(api.hasRow(i));
  }

  static void check(boolean ok) {
    if (!ok) throw new AssertionError();
  }
}
'''

case_messages = {
    "CRASH": "crash/retry created duplicate external upserts or failed to resume all original rows",
    "SNAPSHOT": "job snapshot was not durably pinned before side effects; a post-start row leaked in or an original row was lost",
    "TIES": "stable ordering/resume lost a row when multiple source rows shared the same ordering timestamp",
    "CONCURRENT": "concurrent resume of the same job did not converge to one logical external upsert per row",
}

result = {
    "compiles": False,
    "cases": {name: False for name in case_messages},
    "compiler_output": "",
    "raw_output": "",
}

with tempfile.TemporaryDirectory(prefix="frontier-import-validator-") as td:
    td = Path(td)
    test = td / "FrontierImportResumeHiddenTest.java"
    test.write_text(hidden)
    src = sorted((root / "src").glob("*.java"))
    cp = subprocess.run(
        ["javac", "-d", str(td), *map(str, src), str(test)],
        capture_output=True,
        text=True,
    )
    result["compiler_output"] = (cp.stdout or "") + (cp.stderr or "")
    result["compiles"] = cp.returncode == 0

    if cp.returncode == 0:
        run = subprocess.run(
            ["java", "-cp", str(td), "FrontierImportResumeHiddenTest"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        raw = (run.stdout or "") + (run.stderr or "")
        result["raw_output"] = raw
        for name in case_messages:
            result["cases"][name] = f"{name}_PASS" in raw

if json_mode:
    print(json.dumps(result))
    raise SystemExit(0 if result["compiles"] else 2)

if not result["compiles"]:
    print("VALIDATION_FAIL compile: production sources no longer compile")
    raise SystemExit(1)

for name, message in case_messages.items():
    if not result["cases"][name]:
        print(f"VALIDATION_FAIL {name.lower()}: {message}")
        raise SystemExit(1)

print("VALIDATION_PASS: crash recovery, pinned snapshot, ordering ties, and concurrent resume all converge")
