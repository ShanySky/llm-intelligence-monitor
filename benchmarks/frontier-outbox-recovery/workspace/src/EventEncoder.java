public final class EventEncoder {
    public String confirmed(Order order) {
        return "order_key:" + order.orderKey
            + "|status:" + order.status
            + "|version:" + order.version;
    }
}
