import java.util.HashSet;
import java.util.Set;

public final class JobState {
    final String jobId;
    final Set<String> completed = new HashSet<>();
    boolean cancelRequested = false;

    JobState(String jobId) {
        this.jobId = jobId;
    }

    public boolean isCompleted(String stepId) {
        return completed.contains(stepId);
    }

    public boolean cancelRequested() {
        return cancelRequested;
    }
}
