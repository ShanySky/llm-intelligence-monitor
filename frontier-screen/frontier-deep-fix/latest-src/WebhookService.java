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
    public void paid(String eventId, String orderId, long version) {
        // Event receipt is not proof that fulfillment completed: the process may
        // have failed after recording the event or after the external reservation.
        if (!events.exists(eventId)) events.insert(eventId);

        OrderState state = states.getOrCreate(orderId);
        // Out-of-order events must not roll the order back. Equal versions can
        // still need to resume fulfillment after a prior partial failure.
        if (version < state.version) return;
        if (version > state.version) {
            state.version = version;
            state.status = "PAID";
        }

        String operationKey = "order:" + orderId + ":version:" + version;
        Fulfillment f = fulfillments.findOrCreate(operationKey, orderId);
        if (f.completed) return;

        // The operation key is stable across provider event IDs and retries;
        // this is essential when reserve succeeded but local completion did not.
        String key = "fulfillment:" + orderId + ":version:" + version;
        String reservation = inventory.reserve(orderId, key);
        failure.afterReserve(orderId);

        f.reservationKey = reservation;
        f.completed = true;
    }
}
