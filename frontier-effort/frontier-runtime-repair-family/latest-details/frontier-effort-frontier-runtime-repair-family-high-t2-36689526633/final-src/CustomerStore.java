import java.util.*;

public final class CustomerStore {
    private final Map<Long,String> names = new HashMap<>();
    private final Map<Long,String> stableKeys = new HashMap<>();

    public void create(long id, String stableKey, String name) {
        stableKeys.put(id, stableKey); names.put(id, name);
    }
    public String name(long id) { return names.get(id); }
    public String stableKey(long id) { return stableKeys.get(id); }
    public void update(long id, String name) { names.put(id, name); }
}
