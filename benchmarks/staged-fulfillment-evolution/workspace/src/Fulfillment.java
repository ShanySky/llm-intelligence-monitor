public final class Fulfillment {
    final String eventId;
    final String orderId;
    final long version;
    final String lineItemId;
    String reservationKey;
    boolean completed;

    Fulfillment(String eventId, String orderId, long version, String lineItemId) {
        this.eventId = eventId;
        this.orderId = orderId;
        this.version = version;
        this.lineItemId = lineItemId;
    }
}
