public interface FailureInjector {
    /**
     * Test/runtime hook invoked after the external reservation returned, before
     * the caller necessarily made local completion state durable.
     */
    void afterReserve(String orderId);

    static FailureInjector none() {
        return orderId -> {};
    }
}
