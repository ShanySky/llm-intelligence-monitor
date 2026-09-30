import java.util.*;

public final class CheckpointStore {
    private final Map<String, Checkpoint> checkpoints = new HashMap<>();
    private final Map<String, Object> jobLocks = new HashMap<>();

    public synchronized Checkpoint getOrCreate(String jobId) {
        return checkpoints.computeIfAbsent(jobId, k -> new Checkpoint()).copy();
    }

    public synchronized void save(String jobId, Checkpoint checkpoint) {
        checkpoints.put(jobId, checkpoint.copy());
    }

    synchronized Object lockFor(String jobId) {
        return jobLocks.computeIfAbsent(jobId, k -> new Object());
    }
}
