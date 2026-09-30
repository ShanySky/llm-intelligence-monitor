import java.util.*;

public final class CheckpointStore {
    private final Map<String, Checkpoint> checkpoints = new HashMap<>();

    public synchronized Checkpoint getOrCreate(String jobId) {
        return checkpoints.computeIfAbsent(jobId, k -> new Checkpoint()).copy();
    }

    /** Atomically fixes a job's source watermark the first time it is observed. */
    public synchronized Checkpoint getOrCreate(String jobId, ImportSource source) {
        Checkpoint checkpoint = checkpoints.computeIfAbsent(jobId, k -> new Checkpoint());
        if (checkpoint.snapshot < 0) {
            checkpoint.snapshot = source.snapshot();
        }
        return checkpoint.copy();
    }

    public synchronized void save(String jobId, Checkpoint checkpoint) {
        Checkpoint existing = checkpoints.get(jobId);
        if (existing == null) {
            checkpoints.put(jobId, checkpoint.copy());
            return;
        }
        // A stale concurrent worker must never move durable progress backwards.
        if (existing.snapshot < 0 && checkpoint.snapshot >= 0) {
            existing.snapshot = checkpoint.snapshot;
        }
        if (checkpoint.offset > existing.offset) {
            existing.offset = checkpoint.offset;
            existing.beforeCreatedAt = checkpoint.beforeCreatedAt;
            existing.beforeId = checkpoint.beforeId;
        }
    }
}
