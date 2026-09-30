public interface FailureInjector {
    default void afterExternalEffect(String jobId, long token) {}

    static FailureInjector none() {
        return new FailureInjector() {};
    }
}
