import java.util.*;

public final class OrderStore {
    private final Map<String, OrderRecord> rows = new HashMap<>();

    public synchronized OrderRecord getOrCreate(String id) {
        return rows.computeIfAbsent(id, OrderRecord::new);
    }

    public synchronized OrderRecord get(String id) {
        return rows.get(id);
    }
}
