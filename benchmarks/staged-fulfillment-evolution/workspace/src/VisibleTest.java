public final class VisibleTest {
    public static void main(String[] args) {
        FulfillmentRepository repo = new FulfillmentRepository();
        InventoryClient inventory = new InventoryClient();
        FulfillmentService service = new FulfillmentService(repo, inventory);

        Fulfillment f = service.paid("evt-1", "order-1", 1, "line-a", FailureInjector.none());
        check(f.completed);
        check(inventory.effectCount() == 1);
        check(repo.size() == 1);
        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
