public class WebhookService {
    private final EventRepository events;
    private final FulfillmentRepository fulfillments;
    private final InventoryClient inventory;

    @Transactional
    public void paid(String eventId, String orderId) {
        if (events.exists(eventId)) {
            return;
        }
        events.insert(eventId);

        Fulfillment f = fulfillments.findOrCreate(eventId, orderId);
        if (f.isCompleted()) {
            return;
        }

        String reservationKey = inventory.reserve(orderId, "event:" + eventId);
        f.complete(reservationKey);
    }
}
