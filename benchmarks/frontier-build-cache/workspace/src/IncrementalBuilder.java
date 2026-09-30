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

            String fingerprint = hash(module.source);
            BuildCache.Entry cached = cache.get(name);
            if (cached != null && cached.fingerprint().equals(fingerprint)) {
                return cached.artifact();
            }

            // Remember the new fingerprint before compiling so concurrent callers
            // do not duplicate work.
            cache.put(name, fingerprint, cached == null ? null : cached.artifact());

            Artifact artifact = compiler.compile(module, deps, fingerprint);
            cache.put(name, fingerprint, artifact);
            return artifact;
        } finally {
            stack.remove(name);
        }
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
