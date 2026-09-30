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
        events.record(eventId);

        OrderState state = states.getOrCreate(orderId);
        synchronized (state) {
            if (version < state.version
                    || (version == state.version && "CANCELLED".equals(state.status))) {
                return;
            }
            if (version > state.version) {
                state.version = version;
                state.status = "PAID";
            }

            // A business order has one fulfillment, independent of delivery event IDs.
            Fulfillment f = fulfillments.getOrCreate(orderId, orderId);
            if (f.completed) {
                return;
            }

            // Stable across retries, events, and crashes after the external call.
            String key = inventory.reserve(orderId, reservationKey(orderId));
            failure.afterReserve(orderId);

            f.reservationKey = key;
            f.completed = true;
        }
    }

    public void cancelled(String eventId, String orderId, long version) {
        events.record(eventId);

        OrderState state = states.getOrCreate(orderId);
        synchronized (state) {
            if (version < state.version
                    || (version == state.version && "PAID".equals(state.status))) {
                return;
            }
            if (version > state.version) {
                state.version = version;
                state.status = "CANCELLED";
            }

            // Release by the deterministic external key even if a crash happened
            // before the reservation key was copied into local fulfillment state.
            inventory.release(reservationKey(orderId));
            Fulfillment f = fulfillments.get(orderId);
            if (f != null) {
                f.reservationKey = null;
                f.completed = false;
            }
        }
    }

    private static String reservationKey(String orderId) {
        return "order:" + orderId;
    }
}
