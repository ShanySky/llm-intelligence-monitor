public final class VisibleTest {
    public static void main(String[] args) {
        CustomerStore store=new CustomerStore();
        store.put(new Customer(1,"key-1","OPEN",1));
        new V2CustomerService(store).update(1,"PAID");
        Customer c=store.get(1);
        if(!"PAID".equals(c.newStatus) || c.version!=2) throw new AssertionError();
        System.out.println("VISIBLE_TEST_PASS");
    }
}
