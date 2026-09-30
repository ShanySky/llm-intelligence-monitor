import java.util.HashMap;
import java.util.Map;

public final class Cache<K,V> {
    private final Map<K,V> values = new HashMap<>();

    public V get(K key, Loader<K,V> loader) {
        V value = values.get(key);
        if (value != null) {
            return value;
        }

        try {
            value = loader.load(key);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        values.put(key, value);
        return value;
    }

    public void invalidate(K key) {
        values.remove(key);
    }

    public int size() {
        return values.size();
    }
}
