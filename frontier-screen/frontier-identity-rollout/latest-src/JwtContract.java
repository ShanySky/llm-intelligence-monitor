public final class JwtContract {
    public String claims(Customer c) {
        return "customer_id=" + c.id + "&customer_key=" + c.customerKey;
    }
}
