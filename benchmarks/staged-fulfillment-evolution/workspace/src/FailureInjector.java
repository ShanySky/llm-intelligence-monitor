public interface FailureInjector {
    default void afterReserve(String orderId) {}

    static FailureInjector none() {
        return new FailureInjector() {};
    }
}
