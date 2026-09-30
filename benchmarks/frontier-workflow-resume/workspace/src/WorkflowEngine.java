import java.util.UUID;

public final class WorkflowEngine {
    private final JobStore store;
    private final FailureInjector failure;

    public WorkflowEngine(JobStore store, FailureInjector failure) {
        this.store = store;
        this.failure = failure;
    }

    public void requestCancel(String jobId) {
        store.getOrCreate(jobId).cancelRequested = true;
    }

    public void execute(String jobId, Workflow workflow, StepRunner runner) {
        JobState state = store.getOrCreate(jobId);

        for (Step step : workflow.steps()) {
            if (state.cancelRequested) {
                return;
            }
            if (state.completed.contains(step.id())) {
                continue;
            }

            try {
                runner.run(step.id(), UUID.randomUUID().toString());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }

            failure.afterRunnerSuccess(jobId, step.id());
            state.completed.add(step.id());
        }
    }
}
