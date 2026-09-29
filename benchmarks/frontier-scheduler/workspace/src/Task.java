import java.util.List;

public record Task(String id, int duration, List<String> dependencies, boolean needsGpu) {
    public Task {
        dependencies = List.copyOf(dependencies);
    }
}
