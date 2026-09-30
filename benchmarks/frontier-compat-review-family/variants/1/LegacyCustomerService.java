public final class LegacyCustomerService {
  private final CustomerStore store;
  private final CustomerCache cache;

  public void rename(long id, String name) {
    Customer current = store.get(id);
    Customer replacement = new Customer(id, name, null, current.version + 1);
    store.save(replacement);
    cache.invalidateLegacy(id);
  }
}
