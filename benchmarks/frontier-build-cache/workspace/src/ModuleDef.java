import java.util.List;

public final class ModuleDef {
    final String name;
    String source;
    final List<String> dependencies;

    public ModuleDef(String name, String source, List<String> dependencies) {
        this.name = name;
        this.source = source;
        this.dependencies = List.copyOf(dependencies);
    }
}
