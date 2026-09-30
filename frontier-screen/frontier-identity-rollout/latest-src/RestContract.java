public final class RestContract {
    public String encode(Customer c) {
        return "{\"customer_id\":" + c.id + ",\"customer_key\":\"" + c.customerKey + "\",\"name\":\"" + c.name + "\"}";
    }
}
