public final class LegacyCustomerService {
    private final CustomerStore store;
    public LegacyCustomerService(CustomerStore store){ this.store=store; }

    public void update(long id,String status) {
        store.updateLegacy(id,status);
    }
}
