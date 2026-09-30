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
            runLocked(jobId, failure);
        }
    }

    private void runLocked(String jobId, FailureInjector failure) {
        Checkpoint checkpoint = checkpoints.getOrCreate(jobId);
        if (checkpoint.snapshot < 0) {
            checkpoint.snapshot = source.snapshot();
            checkpoints.save(jobId, checkpoint);
        }

        while (true) {
            List<ImportRow> page = source.pageByOffset(checkpoint.offset, 2, checkpoint.snapshot);
            if (page.isEmpty()) return;

            for (ImportRow row : page) {
                // The key identifies this row in this job and is stable across retries.
                api.upsert(row.id, jobId + ":" + row.ingestSeq, row.value);
                failure.afterUpsert(row.id);

                checkpoint.offset += 1;
                checkpoints.save(jobId, checkpoint);
            }
        }
    }
}
