import java.util.*;

public final class CustomerStore {
    private final Map<Long, Customer> rows = new HashMap<>();

    public synchronized Customer getOrCreate(long id, String name) {
        return rows.computeIfAbsent(id, k -> new Customer(id, name));
    }

    public synchronized Customer get(long id) {
        return rows.get(id);
    }
}
