public final class CustomerCache {
  private final Map<String,Customer> entries = new HashMap<>();

  public void invalidateLegacy(long id) {
    entries.remove("id:" + id);
  }

  public Customer getByStableKey(String key) {
    return entries.get("key:" + key);
  }
}
