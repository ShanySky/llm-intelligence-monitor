public final class LegacyCustomerService {
    private final CustomerStore store;
    public LegacyCustomerService(CustomerStore store){ this.store=store; }

    public void update(long id,String status) {
        synchronized (store) {
            Customer current=store.get(id);
            // The legacy writer owns only legacyStatus and version. Retain
            // identity and fields introduced by newer writers.
            current.legacyStatus=status;
            current.version++;
        }
    }
}
