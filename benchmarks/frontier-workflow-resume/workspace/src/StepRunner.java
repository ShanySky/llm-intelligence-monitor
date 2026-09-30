@FunctionalInterface
public interface StepRunner {
    void run(String stepId, String idempotencyKey) throws Exception;
}
