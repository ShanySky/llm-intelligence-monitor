public final class VerifierCache {
  private final Map<String,Key> cache = new HashMap<>();

  public Key resolve(String issuer, String kid, long registryRevision) {
    return cache.computeIfAbsent(kid, k -> registry.lookup(issuer, kid));
  }
}
