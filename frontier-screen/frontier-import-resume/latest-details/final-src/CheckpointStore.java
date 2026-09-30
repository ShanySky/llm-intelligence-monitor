import java.util.*;

public final class CheckpointStore {
    private final Map<String, Checkpoint> checkpoints = new HashMap<>();

    public synchronized Checkpoint getOrCreate(String jobId) {
        return checkpoints.computeIfAbsent(jobId, k -> new Checkpoint()).copy();
    }

    public synchronized void save(String jobId, Checkpoint checkpoint) {
        checkpoints.put(jobId, checkpoint.copy());
    }
}
