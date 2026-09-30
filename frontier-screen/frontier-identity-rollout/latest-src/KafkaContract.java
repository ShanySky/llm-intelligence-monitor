public final class KafkaContract {
    public String event(Customer c) {
        return "customer_id:" + c.id + "|customer_key:" + c.customerKey + "|name:" + c.name;
    }
}
