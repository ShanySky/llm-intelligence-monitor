import java.util.*;

public final class Workspace {
    private final Map<String, ModuleDef> modules = new HashMap<>();

    public synchronized void add(String name, String source, String... dependencies) {
        modules.put(name, new ModuleDef(name, source, List.of(dependencies)));
    }

    public synchronized void updateSource(String name, String source) {
        ModuleDef m = modules.get(name);
        if (m == null) throw new IllegalArgumentException("unknown module: " + name);
        m.source = source;
    }

    public synchronized ModuleDef get(String name) {
        ModuleDef m = modules.get(name);
        if (m == null) throw new IllegalArgumentException("unknown module: " + name);
        return new ModuleDef(m.name, m.source, m.dependencies);
    }
}
