public final class LegacyCustomerService {
    private final CustomerStore store;
    public LegacyCustomerService(CustomerStore store){ this.store=store; }

    public void update(long id,String status) {
        Customer old=store.get(id);
        Customer replacement=new Customer(id,null,status,old.version+1);
        store.put(replacement);
    }
}
