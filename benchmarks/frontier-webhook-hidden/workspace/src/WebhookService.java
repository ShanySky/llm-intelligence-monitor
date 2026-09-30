public final class WebhookService {
    private final EventLog events;
    private final FulfillmentRepo fulfillments;
    private final OrderStateRepo states;
    private final InventoryClient inventory;
    private final FailureInjector failure;

    public WebhookService(
            EventLog events,
            FulfillmentRepo fulfillments,
            OrderStateRepo states,
            InventoryClient inventory,
            FailureInjector failure) {
        this.events = events;
        this.fulfillments = fulfillments;
        this.states = states;
        this.inventory = inventory;
        this.failure = failure;
    }

    public void paid(String eventId, String orderId, long version) {
        if (!events.record(eventId)) {
            return;
        }

        OrderState state = states.getOrCreate(orderId);
        if (version < state.version) {
            return;
        }
        state.version = version;
        state.status = "PAID";

        Fulfillment f = fulfillments.getOrCreate(eventId, orderId);
        if (f.completed) {
            return;
        }

        String key = inventory.reserve(orderId, "event:" + eventId);
        failure.afterReserve(orderId);

        f.reservationKey = key;
        f.completed = true;
    }

    public void cancelled(String eventId, String orderId, long version) {
        if (!events.record(eventId)) {
            return;
        }

        OrderState state = states.getOrCreate(orderId);
        if (version < state.version) {
            return;
        }
        state.version = version;
        state.status = "CANCELLED";

        Fulfillment f = fulfillments.get(orderId);
        if (f != null && f.reservationKey != null) {
            inventory.release(f.reservationKey);
        }
    }
}
