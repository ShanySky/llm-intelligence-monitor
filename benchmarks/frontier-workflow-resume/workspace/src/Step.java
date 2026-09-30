import java.util.List;

public record Step(String id, List<String> dependencies) {
    public Step {
        dependencies = List.copyOf(dependencies);
    }
}
