public final class LegacyOrderConsumer {
    public boolean accepts(String payload) {
        return payload != null
            && payload.contains("order_id:")
            && payload.contains("status:CONFIRMED");
    }
}
