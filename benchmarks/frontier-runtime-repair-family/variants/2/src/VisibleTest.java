public final class VisibleTest {
    public static void main(String[] args) {
        CustomerStore store=new CustomerStore();
        CustomerCache cache=new CustomerCache();
        store.create(1,"k1","alice");
        CustomerService service=new CustomerService(store,cache);
        if(!"alice".equals(service.readV2(1))) throw new AssertionError();

        ReadRepository repo=new ReadRepository("v1");
        StrictCustomerReader reader=new StrictCustomerReader(repo);
        if(!"v1".equals(reader.ordinaryRead())) throw new AssertionError();
        System.out.println("VISIBLE_TEST_PASS");
    }
}
