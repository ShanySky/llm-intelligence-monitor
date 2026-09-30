import java.util.*;

public final class BuildCache {
    public record Entry(String fingerprint, Artifact artifact) {}

    private final Map<String, Entry> entries = new HashMap<>();

    public synchronized Entry get(String module) {
        return entries.get(module);
    }

    public synchronized void put(String module, String fingerprint, Artifact artifact) {
        entries.put(module, new Entry(fingerprint, artifact));
    }
}
