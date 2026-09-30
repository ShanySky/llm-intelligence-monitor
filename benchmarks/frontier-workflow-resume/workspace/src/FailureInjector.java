public interface FailureInjector {
    void afterRunnerSuccess(String jobId, String stepId);

    static FailureInjector none() {
        return (jobId, stepId) -> {};
    }
}
