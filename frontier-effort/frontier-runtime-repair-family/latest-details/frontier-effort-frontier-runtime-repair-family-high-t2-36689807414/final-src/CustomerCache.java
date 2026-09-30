import java.util.*;

public final class CustomerCache {
    private final Map<String,String> values = new HashMap<>();
    public String get(String key) { return values.get(key); }
    public void put(String key,String value) { values.put(key,value); }
    public void evict(String key) { values.remove(key); }
    public void clear() { values.clear(); }
}
