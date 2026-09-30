import java.util.List;

public record Workflow(List<Step> steps) {
    public Workflow {
        steps = List.copyOf(steps);
    }
}
