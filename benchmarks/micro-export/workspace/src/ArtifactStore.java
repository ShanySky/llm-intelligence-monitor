import java.util.LinkedHashMap;
import java.util.Map;

public final class ArtifactStore {
    private final Map<String, String> objects = new LinkedHashMap<>();
    private int sequence = 0;

    public String uploadNew(String jobId, String content) {
        String key = jobId + "-" + (++sequence) + ".txt";
        objects.put(key, content);
        return key;
    }

    public String putIfAbsent(String key, String content) {
        objects.putIfAbsent(key, content);
        return key;
    }

    public boolean exists(String key) {
        return objects.containsKey(key);
    }

    public String get(String key) {
        return objects.get(key);
    }

    public int countForJob(String jobId) {
        int count = 0;
        for (String key : objects.keySet()) {
            if (key.startsWith(jobId + "-") || key.equals(jobId + ".txt")) {
                count++;
            }
        }
        return count;
    }

    public String firstKeyForJob(String jobId) {
        for (String key : objects.keySet()) {
            if (key.startsWith(jobId + "-") || key.equals(jobId + ".txt")) {
                return key;
            }
        }
        return null;
    }
}
