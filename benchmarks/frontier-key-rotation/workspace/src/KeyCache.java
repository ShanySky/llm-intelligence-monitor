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

    private final Map<String, Entry> entries = new HashMap<>();

    public synchronized KeyVersion getOrLoad(
            String issuer, long revision, String kid, Supplier<KeyVersion> loader) {
        Entry cached = entries.get(kid);
        if (cached != null) {
            return cached.key;
        }
        KeyVersion loaded = loader.get();
        if (loaded != null) {
            entries.put(kid, new Entry(revision, loaded));
        }
        return loaded;
    }
}
