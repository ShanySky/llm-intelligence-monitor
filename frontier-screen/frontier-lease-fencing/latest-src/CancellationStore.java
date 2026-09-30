import java.util.*;

public final class CancellationStore {
    private final Set<String> cancelled = new HashSet<>();

    public synchronized void cancel(String jobId) {
        cancelled.add(jobId);
    }

    public synchronized boolean isCancelled(String jobId) {
        return cancelled.contains(jobId);
    }
}
