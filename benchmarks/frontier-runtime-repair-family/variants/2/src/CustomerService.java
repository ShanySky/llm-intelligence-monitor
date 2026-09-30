public final class CustomerService {
    private final CustomerStore store;
    private final CustomerCache cache;

    public CustomerService(CustomerStore store, CustomerCache cache) {
        this.store = store; this.cache = cache;
    }

    public String readV2(long id) {
        String key = "stable:" + store.stableKey(id);
        String value = cache.get(key);
        if (value == null) {
            value = store.name(id);
            cache.put(key, value);
        }
        return value;
    }

    public void legacyUpdate(long id, String name) {
        store.update(id, name);
        cache.evict("legacy:" + id);
    }

    public void v2Update(long id, String name) {
        store.update(id, name);
        cache.evict("legacy:" + id);
        cache.evict("stable:" + store.stableKey(id));
    }
}
