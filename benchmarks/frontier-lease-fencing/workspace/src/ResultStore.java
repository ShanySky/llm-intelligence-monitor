import java.util.*;

public final class ResultStore {
    private final Map<String, String> values = new HashMap<>();
    private final Map<String, Long> tokens = new HashMap<>();

    public synchronized void save(String jobId, long token, String value) {
        values.put(jobId, value);
        tokens.put(jobId, token);
    }

    public synchronized String get(String jobId) {
        return values.get(jobId);
    }

    public synchronized long token(String jobId) {
        return tokens.getOrDefault(jobId, 0L);
    }
}
