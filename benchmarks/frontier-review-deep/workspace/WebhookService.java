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
        if (events.exists(eventId)) return;
        events.insert(eventId);

        OrderState state = states.getOrCreate(orderId);
        if (version < state.version) return;
        state.version = version;
        state.status = "PAID";

        Fulfillment f = fulfillments.findOrCreate(eventId, orderId);
        if (f.completed) return;

        String key = inventory.reserve(orderId, "event:" + eventId);
        failure.afterReserve(orderId);

        f.reservationKey = key;
        f.completed = true;
    }
}
