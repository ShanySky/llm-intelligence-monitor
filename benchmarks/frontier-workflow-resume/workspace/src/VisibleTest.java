import java.util.ArrayList;
import java.util.List;

public final class VisibleTest {
    public static void main(String[] args) {
        JobStore store = new JobStore();
        WorkflowEngine engine = new WorkflowEngine(store, FailureInjector.none());
        List<String> ran = new ArrayList<>();

        Workflow wf = new Workflow(List.of(
            new Step("A", List.of()),
            new Step("B", List.of("A"))
        ));

        engine.execute("job-visible", wf, (step, key) -> ran.add(step));

        if (!ran.equals(List.of("A", "B"))) {
            throw new AssertionError("basic workflow");
        }
        if (!store.get("job-visible").isCompleted("A") ||
            !store.get("job-visible").isCompleted("B")) {
            throw new AssertionError("completion state");
        }

        System.out.println("VISIBLE_TEST_PASS");
    }
}
