public final class IdentityService {
    private final CustomerStore store;

    public IdentityService(CustomerStore store) {
        this.store = store;
    }

    public String customerKey(long id) {
        Customer c = store.get(id);
        if (c == null) return null;
        if (c.customerKey == null) {
            return "customer-" + id + "-" + System.nanoTime();
        }
        return c.customerKey;
    }

    public Customer createV2(long id, String key, String name) {
        Customer c = store.getOrCreate(id, name);
        c.customerKey = key;
        c.name = name;
        return c;
    }
}
