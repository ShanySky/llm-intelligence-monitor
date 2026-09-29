public final class OrderState {
    final String orderId;
    long version = -1;
    String status = "UNKNOWN";

    OrderState(String orderId) {
        this.orderId = orderId;
    }
}
