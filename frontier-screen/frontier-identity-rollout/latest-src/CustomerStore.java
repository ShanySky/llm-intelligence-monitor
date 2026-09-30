import java.util.*;

public final class CustomerStore {
    private final Map<Long, Customer> rows = new HashMap<>();

    public synchronized Customer getOrCreate(long id, String name) {
        return rows.computeIfAbsent(id, k -> new Customer(id, name));
    }

    public synchronized Customer get(long id) {
        return rows.get(id);
    }

    /** Assign a key only when absent, so concurrent readers and old writers cannot replace it. */
    synchronized String ensureCustomerKey(long id, String candidate) {
        Customer c = rows.get(id);
        if (c == null) return null;
        if (c.customerKey == null) c.customerKey = candidate;
        return c.customerKey;
    }

    synchronized Customer updateV2(long id, String key, String name) {
        Customer c = getOrCreate(id, name);
        if (c.customerKey == null) c.customerKey = key;
        c.name = name;
        return c;
    }
}
