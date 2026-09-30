public final class LegacyCustomerService {
    private final CustomerStore store;
    public LegacyCustomerService(CustomerStore store){ this.store=store; }

    public void update(long id,String status) {
        synchronized (store) {
            Customer old=store.get(id);
            Customer replacement=new Customer(id,old.stableKey,status,old.version+1);
            store.put(replacement);
        }
    }
}
