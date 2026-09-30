public final class RedeliveryProbe {
    public static void main(String[] args) {
        FulfillmentRepository repo = new FulfillmentRepository();
        InventoryClient inventory = new InventoryClient();
        FulfillmentService service = new FulfillmentService(repo, inventory);

        service.paid("evt-1", "order-3", 7, "line-a", FailureInjector.none());
        service.paid("evt-2", "order-3", 7, "line-a", FailureInjector.none());

        if (inventory.effectCount() != 1) throw new AssertionError("redelivery duplicated effect");
        if (repo.size() != 1) throw new AssertionError("redelivery duplicated local fulfillment");

        service.paid("evt-3", "order-3", 8, "line-a", FailureInjector.none());
        if (inventory.effectCount() != 2) throw new AssertionError("new version collapsed");
        if (repo.size() != 2) throw new AssertionError("new version collapsed locally");

        System.out.println("REDELIVERY_PASS");
    }
}
