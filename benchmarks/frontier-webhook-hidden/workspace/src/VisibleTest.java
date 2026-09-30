public final class VisibleTest {
    public static void main(String[] args) {
        EventLog events = new EventLog();
        FulfillmentRepo fulfillments = new FulfillmentRepo();
        OrderStateRepo states = new OrderStateRepo();
        InventoryClient inventory = new InventoryClient();
        WebhookService service = new WebhookService(
                events, fulfillments, states, inventory, FailureInjector.none());

        service.paid("evt-visible", "order-visible", 1);

        if (inventory.reservationCount() != 1) {
            throw new AssertionError("happy path must reserve once");
        }
        if (!"PAID".equals(states.get("order-visible").status)) {
            throw new AssertionError("order must be PAID");
        }

        System.out.println("VISIBLE_TEST_PASS");
    }
}
