import java.util.*;
import java.util.UUID;

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
        Checkpoint checkpoint = checkpoints.getOrCreate(jobId);

        while (true) {
            List<ImportRow> page = source.pageByOffset(checkpoint.offset, 2);
            if (page.isEmpty()) {
                return;
            }

            for (ImportRow row : page) {
                api.upsert(row.id, UUID.randomUUID().toString(), row.value);
                failure.afterUpsert(row.id);

                checkpoint.offset += 1;
                checkpoints.save(jobId, checkpoint);
            }
        }
    }
}
