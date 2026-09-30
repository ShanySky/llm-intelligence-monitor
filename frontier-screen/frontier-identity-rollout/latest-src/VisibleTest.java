public final class VisibleTest {
    public static void main(String[] args) {
        CustomerStore store = new CustomerStore();
        IdentityService identities = new IdentityService(store);
        V2CustomerService v2 = new V2CustomerService(store, identities);

        Customer c = v2.write(7L, "ck-7", "Ada");
        if (!"ck-7".equals(v2.key(c))) {
            throw new AssertionError("v2 key");
        }

        System.out.println("VISIBLE_TEST_PASS");
    }
}
