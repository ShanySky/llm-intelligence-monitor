import java.util.HashMap;
import java.util.Map;

public final class JobStore {
    private final Map<String, JobState> jobs = new HashMap<>();

    public synchronized JobState getOrCreate(String jobId) {
        return jobs.computeIfAbsent(jobId, JobState::new);
    }

    public synchronized JobState get(String jobId) {
        return jobs.get(jobId);
    }
}
