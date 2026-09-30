public final class WebhookService {
    private final EventRepository events;
    private final OrderStateRepository states;
    private final FulfillmentRepository fulfillments;
    private final InventoryClient inventory;
    private final FailureInjector failure;

    public WebhookService(
        EventRepository events,
        OrderStateRepository states,
        FulfillmentRepository fulfillments,
        InventoryClient inventory,
        FailureInjector failure
    ) {
        this.events = events;
        this.states = states;
        this.fulfillments = fulfillments;
        this.inventory = inventory;
        this.failure = failure;
    }

    @Transactional
    public synchronized void paid(String eventId, String orderId, long version) {
        // Event recording is idempotent, but a previously recorded event must not
        // suppress recovery of fulfillment after a crash.
        synchronized (events) {
            if (!events.exists(eventId)) events.insert(eventId);
        }

        OrderState state = states.getOrCreate(orderId);
        synchronized (state) {
            if (version < state.version) return;
            if (version > state.version) {
                state.version = version;
                state.status = "PAID";
            }

            // Fulfillment is per order, not per provider delivery. The stable key
            // lets inventory deduplicate retries even if the process dies after reserve.
            Fulfillment f = fulfillments.findOrCreate(orderId, orderId);
            synchronized (f) {
                if (f.completed) return;
                String key = inventory.reserve(orderId, "order:" + orderId);
                failure.afterReserve(orderId);
                f.reservationKey = key;
                f.completed = true;
            }
        }
    }
}
