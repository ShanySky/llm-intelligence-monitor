public final class OrderService {
    private final Database db;
    private final EventEncoder encoder;

    public OrderService(Database db, EventEncoder encoder) {
        this.db = db;
        this.encoder = encoder;
    }

    public Order confirm(String orderId, long version, FailureInjector failure) {
        Order order = db.getOrder(orderId);
        if (order == null) throw new IllegalArgumentException("unknown order");
        order.status = "CONFIRMED";
        order.version = version;
        db.saveOrder(order);

        failure.beforeOutbox(orderId);

        String eventId = "confirm-" + orderId + "-" + System.nanoTime();
        db.saveOutbox(new OutboxRecord(
            eventId, orderId, version, encoder.confirmed(order)
        ));
        return order;
    }
}
