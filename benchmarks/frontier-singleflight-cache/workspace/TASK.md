# Task: implement a production-safe single-flight loading cache

This small Java project contains a loading cache used by a multi-threaded service.
The public API is fixed.

Implement the missing behavior in Cache.java.

Requirements:

1. A cached value is returned without invoking the loader again.
2. Concurrent misses for the same key must share one in-flight load. Exactly one
   loader invocation is allowed for that wave of callers, and every caller must
   receive the same result.
3. Different keys must be able to load concurrently; do not serialize the whole
   cache behind one global lock while a loader is running.
4. If invalidate(key) happens while a load for that key is in flight, the
   in-flight callers may still receive that loaded value, but that stale result
   must not repopulate the cache. The next get must load again.
5. If the loader throws, every caller waiting on that in-flight load must observe
   a failure. The failed in-flight state must be removed so a later get can retry.
6. Preserve the existing public class, constructor, and method signatures.
7. Use only the Java standard library.

Run ./run_visible_tests.sh before finishing.
