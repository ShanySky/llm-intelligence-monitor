public final class V2CustomerService {
    private final CustomerStore store;
    public V2CustomerService(CustomerStore store){ this.store=store; }

    public void update(long id,String status) {
        synchronized (store) {
            Customer c=store.get(id);
            c.legacyStatus=status;
            c.newStatus=status;
            c.version++;
        }
    }
}
