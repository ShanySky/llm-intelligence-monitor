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
        Checkpoint checkpoint = checkpoints.getOrCreate(jobId, source);

        while (true) {
            List<ImportRow> page = source.pageByOffset(checkpoint.offset, 2, checkpoint.snapshot);
            if (page.isEmpty()) {
                return;
            }

            for (ImportRow row : page) {
                String idempotencyKey = jobId.length() + ":" + jobId + ":" + row.ingestSeq;
                api.upsert(row.id, idempotencyKey, row.value);
                failure.afterUpsert(row.id);

                checkpoint.offset += 1;
                checkpoints.save(jobId, checkpoint);
            }
        }
    }
}
