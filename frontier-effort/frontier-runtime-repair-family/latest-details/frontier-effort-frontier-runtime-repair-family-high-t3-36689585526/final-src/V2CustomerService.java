public final class V2CustomerService {
    private final CustomerStore store;
    public V2CustomerService(CustomerStore store){ this.store=store; }

    public void update(long id,String status) {
        store.updateV2(id,status);
    }
}
