public final class StrictCustomerReader {
  public Customer readAfterWrite(String customerKey) {
    Customer cached=cache.get(customerKey);
    if(cached!=null) return cached;
    return replica.findByStableKey(customerKey);
  }
}
