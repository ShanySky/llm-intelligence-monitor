public final class RestContract {
    public String encode(Customer c) {
        return "{\"customer_key\":\"" + c.customerKey + "\",\"name\":\"" + c.name + "\"}";
    }
}
