public final class LegacyRestContract {
    public String encode(Customer c) {
        return "{\"customer_id\":" + c.id + ",\"name\":\"" + c.name + "\"}";
    }
}
