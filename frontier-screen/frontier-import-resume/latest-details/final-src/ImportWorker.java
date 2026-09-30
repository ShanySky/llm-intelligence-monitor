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
        synchronized (checkpoints.lockFor(jobId)) {
            Checkpoint checkpoint = checkpoints.getOrCreate(jobId);
            if (checkpoint.snapshot < 0) {
                checkpoint.snapshot = source.snapshot();
                checkpoints.save(jobId, checkpoint);
            }

            while (true) {
                List<ImportRow> page = source.page(checkpoint.snapshot, checkpoint, 2);
                if (page.isEmpty()) return;

                for (ImportRow row : page) {
                    String idempotencyKey = jobId + ":" + row.ingestSeq;
                    api.upsert(row.id, idempotencyKey, row.value);
                    failure.afterUpsert(row.id);

                    checkpoint.offset += 1;
                    checkpoint.beforeCreatedAt = row.createdAt;
                    checkpoint.beforeId = row.id;
                    checkpoint.beforeIngestSeq = row.ingestSeq;
                    checkpoint.hasCursor = true;
                    checkpoints.save(jobId, checkpoint);
                }
            }
        }
    }
}
