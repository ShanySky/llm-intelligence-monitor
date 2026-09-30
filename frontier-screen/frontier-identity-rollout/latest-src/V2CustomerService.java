public final class V2CustomerService {
    private final CustomerStore store;
    private final IdentityService identities;

    public V2CustomerService(CustomerStore store, IdentityService identities) {
        this.store = store;
        this.identities = identities;
    }

    public Customer read(long id) {
        Customer c = store.get(id);
        if (c != null) identities.customerKey(id);
        return c;
    }

    public Customer write(long id, String customerKey, String name) {
        return identities.createV2(id, customerKey, name);
    }

    public String key(Customer c) {
        return identities.customerKey(c.id);
    }
}
