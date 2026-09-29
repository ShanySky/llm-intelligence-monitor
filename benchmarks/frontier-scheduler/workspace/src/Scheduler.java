import java.util.*;

public final class Scheduler {
    public List<ScheduleEntry> plan(List<Task> input, int workerCount) {
        if (workerCount <= 0) {
            throw new IllegalArgumentException("workerCount");
        }

        Map<String, Task> byId = new HashMap<>();
        for (Task t : input) {
            if (t.duration() <= 0 || byId.put(t.id(), t) != null) {
                throw new IllegalArgumentException("invalid task");
            }
        }
        for (Task t : input) {
            for (String dep : t.dependencies()) {
                if (!byId.containsKey(dep)) {
                    throw new IllegalArgumentException("unknown dependency");
                }
            }
        }

        // Current implementation: greedy lexical list scheduling.
        // It is deterministic, but it is not guaranteed to minimize makespan.
        Map<String,Integer> finish = new HashMap<>();
        int[] workerFree = new int[workerCount];
        int gpuFree = 0;
        List<ScheduleEntry> result = new ArrayList<>();
        Set<String> remaining = new HashSet<>(byId.keySet());

        while (!remaining.isEmpty()) {
            List<String> ready = remaining.stream()
                    .filter(id -> byId.get(id).dependencies().stream().allMatch(finish::containsKey))
                    .sorted()
                    .toList();
            if (ready.isEmpty()) {
                throw new IllegalArgumentException("cycle");
            }

            String id = ready.get(0);
            Task t = byId.get(id);
            int depsDone = 0;
            for (String dep : t.dependencies()) {
                depsDone = Math.max(depsDone, finish.get(dep));
            }

            int bestWorker = 0;
            int bestStart = Integer.MAX_VALUE;
            for (int w = 0; w < workerCount; w++) {
                int start = Math.max(workerFree[w], depsDone);
                if (t.needsGpu()) {
                    start = Math.max(start, gpuFree);
                }
                if (start < bestStart) {
                    bestStart = start;
                    bestWorker = w;
                }
            }

            int end = bestStart + t.duration();
            workerFree[bestWorker] = end;
            if (t.needsGpu()) {
                gpuFree = end;
            }
            finish.put(id, end);
            remaining.remove(id);
            result.add(new ScheduleEntry(id, bestStart, end, bestWorker));
        }

        result.sort(Comparator.comparing(ScheduleEntry::id));
        return result;
    }
}
