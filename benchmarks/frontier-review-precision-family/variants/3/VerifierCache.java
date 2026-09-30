public final class VerifierCache {
  private final Map<String,Key> cache=new HashMap<>();
  public Key resolve(String issuer,String kid,long registryRevision) {
    String key=issuer+"|"+kid;
    return cache.computeIfAbsent(key,k->registry.lookup(issuer,kid));
  }
}
