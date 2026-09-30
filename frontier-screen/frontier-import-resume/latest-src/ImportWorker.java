import java.util.*;

public final class ImportWorker {
    private final ImportSource source;
    private final CheckpointStore checkpoints;
    private final CustomerApi api;

    public ImportWorker(ImportSource source, CheckpointStore checkpoints, CustomerApi api) {
        this.source = source;
        this.checkpoints = checkpoints;
        this.api = api;
    }

    public void run(String jobId, FailureInjector failure) {
        // A job has a single durable cursor. Serialize its readers and writers so a
        // stale copy of that cursor can never overwrite newer completed progress.
        synchronized (checkpoints) {
            runSerialized(jobId, failure);
        }
    }

    private void runSerialized(String jobId, FailureInjector failure) {
        Checkpoint checkpoint = checkpoints.getOrCreate(jobId);
        if (checkpoint.snapshot < 0) {
            checkpoint.snapshot = source.snapshot();
            checkpoints.save(jobId, checkpoint);
        }

        while (true) {
            List<ImportRow> page = source.pageAfter(checkpoint.snapshot,
                checkpoint.beforeCreatedAt, checkpoint.beforeId, checkpoint.beforeIngestSeq, 2);
            if (page.isEmpty()) return;

            for (ImportRow row : page) {
                String idempotencyKey = jobId + ":" + row.ingestSeq;
                api.upsert(row.id, idempotencyKey, row.value);
                failure.afterUpsert(row.id);

                checkpoint.offset += 1;
                checkpoint.beforeCreatedAt = row.createdAt;
                checkpoint.beforeId = row.id;
                checkpoint.beforeIngestSeq = row.ingestSeq;
                checkpoints.save(jobId, checkpoint);
            }
        }
    }
}
