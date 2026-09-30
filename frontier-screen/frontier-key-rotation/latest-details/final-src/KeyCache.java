import java.util.*;
import java.util.function.Supplier;

public final class KeyCache {
    private static final class Entry {
        final long revision;
        final KeyVersion key;
        Entry(long revision, KeyVersion key) {
            this.revision = revision;
            this.key = key;
        }
    }

    private final Map<String, Map<String, Entry>> entries = new HashMap<>();

    public synchronized KeyVersion getOrLoad(
            String issuer, long revision, String kid, Supplier<KeyVersion> loader) {
        Map<String, Entry> issuerEntries = entries.computeIfAbsent(issuer, x -> new HashMap<>());
        Entry cached = issuerEntries.get(kid);
        if (cached != null && cached.revision == revision) {
            return cached.key;
        }
        KeyVersion loaded = loader.get();
        if (loaded != null && issuer.equals(loaded.issuer) && kid.equals(loaded.kid)) {
            issuerEntries.put(kid, new Entry(revision, loaded));
            return loaded;
        }
        issuerEntries.remove(kid);
        return null;
    }
}
