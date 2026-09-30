import java.util.*;

public final class Compiler {
    private final Map<String, Integer> builds = new HashMap<>();
    private final Set<String> failNext = new HashSet<>();

    public synchronized void failNext(String module) {
        failNext.add(module);
    }

    public synchronized int buildCount(String module) {
        return builds.getOrDefault(module, 0);
    }

    public synchronized Artifact compile(ModuleDef module, List<Artifact> dependencies, String fingerprint) {
        builds.merge(module.name, 1, Integer::sum);
        if (failNext.remove(module.name)) {
            throw new IllegalStateException("transient compile failure: " + module.name);
        }

        StringBuilder out = new StringBuilder();
        out.append(module.name).append("{").append(module.source).append("}");
        for (Artifact dep : dependencies) {
            out.append("<").append(dep.output()).append(">");
        }
        return new Artifact(module.name, fingerprint, out.toString());
    }
}
