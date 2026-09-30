public final class Fulfillment {
    final String orderId;
    boolean completed;
    String reservationKey;

    public Fulfillment(String orderId) {
        this.orderId = orderId;
    }
}
