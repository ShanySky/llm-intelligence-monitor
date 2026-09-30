public interface FailureInjector {
    default void afterCharge() {}
    static FailureInjector none() { return new FailureInjector() {}; }
}
