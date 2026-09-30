import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

public final class IncrementalBuilder {
    private final Workspace workspace;
    private final BuildCache cache;
    private final Compiler compiler;

    public IncrementalBuilder(Workspace workspace, BuildCache cache, Compiler compiler) {
        this.workspace = workspace;
        this.cache = cache;
        this.compiler = compiler;
    }

    public Artifact build(String target) {
        return build(target, new LinkedHashSet<>());
    }

    private Artifact build(String name, Set<String> stack) {
        if (!stack.add(name)) {
            throw new IllegalArgumentException("dependency cycle: " + stack + " -> " + name);
        }

        try {
            ModuleDef module = workspace.get(name);
            List<Artifact> deps = new ArrayList<>();
            for (String dependency : module.dependencies) {
                deps.add(build(dependency, stack));
            }

            StringBuilder inputs = new StringBuilder();
            appendPart(inputs, module.source);
            for (Artifact dependency : deps) {
                appendPart(inputs, dependency.fingerprint());
            }
            String fingerprint = hash(inputs.toString());
            BuildCache.Entry cached = cache.get(name);
            if (cached != null && cached.artifact() != null
                    && cached.fingerprint().equals(fingerprint)) {
                return cached.artifact();
            }

            // Publish only successful results. A failed compile must leave the
            // prior usable cache entry intact (or leave the module uncached).
            Artifact artifact = compiler.compile(module, deps, fingerprint);
            cache.put(name, fingerprint, artifact);
            return artifact;
        } finally {
            stack.remove(name);
        }
    }

    private static void appendPart(StringBuilder out, String part) {
        out.append(part.length()).append(':').append(part);
    }

    private static String hash(String text) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (byte b : bytes) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }
}
