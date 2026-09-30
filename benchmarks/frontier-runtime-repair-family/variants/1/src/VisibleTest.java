public final class VisibleTest {
    public static void main(String[] args) {
        PaymentProvider provider = new PaymentProvider();
        PaymentService service = new PaymentService(provider, FailureInjector.none());
        service.pay("o-1", 1, "d-1");
        service.pay("o-1", 1, "d-1");
        if (provider.effects() != 1) throw new AssertionError("normal retry");
        System.out.println("VISIBLE_TEST_PASS");
    }
}
