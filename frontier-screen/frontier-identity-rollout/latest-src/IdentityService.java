import java.util.UUID;

public final class IdentityService {
    private final CustomerStore store;

    public IdentityService(CustomerStore store) {
        this.store = store;
    }

    public String customerKey(long id) {
        Customer c = store.get(id);
        if (c == null) {
            return null;
        }
        return store.ensureCustomerKey(id, c.customerKey == null ? "ck-" + UUID.randomUUID() : c.customerKey);
    }

    public Customer createV2(long id, String key, String name) {
        return store.updateV2(id, key, name);
    }
}
