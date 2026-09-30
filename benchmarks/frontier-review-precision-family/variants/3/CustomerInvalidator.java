public final class CustomerInvalidator {
  public void afterCommit(Customer c) {
    hooks.afterCommit(() -> {
      cache.remove("id:"+c.legacyId);
      cache.remove("key:"+c.customerKey);
    });
  }
}
