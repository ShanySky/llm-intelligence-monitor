public final class EventEncoder {
    public String confirmed(Order order) {
        return "order_id:" + order.id
            + "|order_key:" + order.orderKey
            + "|status:" + order.status
            + "|version:" + order.version;
    }
}
