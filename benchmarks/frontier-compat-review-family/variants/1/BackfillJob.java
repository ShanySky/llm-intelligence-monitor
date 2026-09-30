public final class BackfillJob {
  private final CustomerStore store;

  public void apply(BackfillItem item) {
    Customer current = store.get(item.id());
    current.customerKey = item.customerKey();
    current.newVersion = item.sourceVersion();
    store.save(current);
  }
}
