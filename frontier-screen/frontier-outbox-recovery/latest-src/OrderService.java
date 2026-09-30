public final class OrderService {
    private final Database db;
    private final EventEncoder encoder;

    public OrderService(Database db, EventEncoder encoder) {
        this.db = db;
        this.encoder = encoder;
    }

    public Order confirm(String orderId, long version, FailureInjector failure) {
        return db.transaction(tx -> {
            Order order = tx.getOrder(orderId);
            if (order == null) throw new IllegalArgumentException("unknown order");

            order.status = "CONFIRMED";
            order.version = version;
            failure.beforeOutbox(orderId);

            // A confirmation is unique for an order/version. Retrying the transaction
            // therefore reuses the same durable event instead of creating another one.
            String eventId = "confirm-" + orderId + "-" + version;
            tx.saveOrder(order);
            tx.saveOutboxIfAbsent(new OutboxRecord(
                eventId, orderId, version, encoder.confirmed(order)
            ));
            return order.copy();
        });
    }
}
