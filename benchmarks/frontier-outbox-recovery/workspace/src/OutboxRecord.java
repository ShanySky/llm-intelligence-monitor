public final class OutboxRecord {
    final String eventId;
    final String orderId;
    final long orderVersion;
    final String payload;
    boolean sent;

    OutboxRecord(String eventId, String orderId, long orderVersion, String payload) {
        this.eventId = eventId;
        this.orderId = orderId;
        this.orderVersion = orderVersion;
        this.payload = payload;
    }

    OutboxRecord copy() {
        OutboxRecord c = new OutboxRecord(eventId, orderId, orderVersion, payload);
        c.sent = sent;
        return c;
    }
}
