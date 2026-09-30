public final class JwtContract {
    public String claims(Customer c) {
        return "customer_key=" + c.customerKey;
    }
}
