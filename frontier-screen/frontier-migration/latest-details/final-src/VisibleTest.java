public final class VisibleTest {
    public static void main(String[] args) {
        OrderStore store = new OrderStore();
        V2OrderService v2 = new V2OrderService(store);

        v2.writeStatus("order-visible", "PAID", "card");
        if (!"PAID".equals(v2.readStatus("order-visible"))) {
            throw new AssertionError("v2 happy path");
        }

        System.out.println("VISIBLE_TEST_PASS");
    }
}
