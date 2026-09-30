import java.util.UUID;

public final class FulfillmentService {
    private final FulfillmentRepository fulfillments;
    private final InventoryClient inventory;

    public FulfillmentService(FulfillmentRepository fulfillments, InventoryClient inventory) {
        this.fulfillments = fulfillments;
        this.inventory = inventory;
    }

    public Fulfillment paid(
        String eventId, String orderId, long version, String lineItemId, FailureInjector failure
    ) {
        Fulfillment f = fulfillments.findOrCreate(eventId, orderId, version, lineItemId);
        if (f.completed) return f;

        String key = inventory.reserve(UUID.randomUUID().toString());
        failure.afterReserve(orderId);

        f.reservationKey = key;
        f.completed = true;
        return f;
    }
}
