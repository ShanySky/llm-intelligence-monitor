public final class V1CustomerService {
    private final CustomerStore store;

    public V1CustomerService(CustomerStore store) {
        this.store = store;
    }

    public Customer write(long id, String name) {
        Customer c = store.getOrCreate(id, name);
        c.name = name;
        return c;
    }

    public long id(Customer c) {
        return c.id;
    }
}
