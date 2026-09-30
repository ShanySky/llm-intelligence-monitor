public final class PartnerCompatibilityProbe {
    public static void main(String[] args) {
        Customer c = new Customer(91L, "Partner");
        c.customerKey = "ck-91";

        String rest = new RestContract().encode(c);
        String jwt = new JwtContract().claims(c);
        String kafka = new KafkaContract().event(c);

        check(rest.contains("customer_id") && rest.contains("91"));
        check(rest.contains("customer_key") && rest.contains("ck-91"));
        check(jwt.contains("customer_id") && jwt.contains("91"));
        check(jwt.contains("customer_key") && jwt.contains("ck-91"));
        check(kafka.contains("customer_id") && kafka.contains("91"));
        check(kafka.contains("customer_key") && kafka.contains("ck-91"));

        System.out.println("PARTNER_COMPATIBILITY_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError("legacy partner field missing");
    }
}
