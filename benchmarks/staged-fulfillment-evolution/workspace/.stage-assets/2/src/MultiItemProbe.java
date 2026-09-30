public final class MultiItemProbe {
    public static void main(String[] args) {
        FulfillmentRepository repo = new FulfillmentRepository();
        InventoryClient inventory = new InventoryClient();
        FulfillmentService service = new FulfillmentService(repo, inventory);

        service.paid("evt-a", "order-2", 4, "line-a", FailureInjector.none());
        service.paid("evt-b", "order-2", 4, "line-b", FailureInjector.none());

        if (inventory.effectCount() != 2) throw new AssertionError("line items collided");
        if (repo.size() != 2) throw new AssertionError("local line items collided");
        System.out.println("MULTI_ITEM_PASS");
    }
}
