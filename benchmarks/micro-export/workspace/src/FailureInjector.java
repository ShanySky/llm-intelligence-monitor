public interface FailureInjector {
    void afterPublish(String jobId);

    static FailureInjector none() {
        return jobId -> {};
    }
}
