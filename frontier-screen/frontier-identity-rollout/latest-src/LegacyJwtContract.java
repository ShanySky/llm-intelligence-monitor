public final class LegacyJwtContract {
    public String claims(Customer c) {
        return "customer_id=" + c.id;
    }
}
