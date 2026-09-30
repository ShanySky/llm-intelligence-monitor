public final class KafkaContract {
    public String event(Customer c) {
        return "customer_key:" + c.customerKey + "|name:" + c.name;
    }
}
