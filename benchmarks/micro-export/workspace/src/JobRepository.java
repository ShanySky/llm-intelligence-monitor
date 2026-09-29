import java.util.HashMap;
import java.util.Map;

public final class JobRepository {
    private final Map<String, ExportJob> jobs = new HashMap<>();

    public ExportJob create(String id) {
        ExportJob job = new ExportJob(id);
        if (jobs.putIfAbsent(id, job) != null) {
            throw new IllegalArgumentException("duplicate job: " + id);
        }
        return job;
    }

    public ExportJob get(String id) {
        ExportJob job = jobs.get(id);
        if (job == null) {
            throw new IllegalArgumentException("missing job: " + id);
        }
        return job;
    }
}
