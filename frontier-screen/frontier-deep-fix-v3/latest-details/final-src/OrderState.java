public final class OrderState {
    final String orderId;
    long version;
    String status;

    public OrderState(String orderId) {
        this.orderId = orderId;
        this.version = -1;
        this.status = "UNKNOWN";
    }
}
