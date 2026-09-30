public final class LegacyKafkaContract {
    public String event(Customer c) {
        return "customer_id:" + c.id + "|name:" + c.name;
    }
}
