public interface FailureInjector {
    default void beforeOutbox(String orderId) {}
    default void afterPublish(String eventId) {}

    static FailureInjector none() {
        return new FailureInjector() {};
    }
}
