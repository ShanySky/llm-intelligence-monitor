public final class ConfirmationService {
  @Transactional
  public void confirm(String orderId,long version) {
    Order row=orders.get(orderId);
    row.version=version;
    row.status="CONFIRMED";
    String eventKey="confirm:"+orderId;
    outbox.insertIfAbsent(eventKey,new ConfirmationEvent(orderId,version));
    TransactionHooks.afterCommit(() -> cache.evict(orderId));
  }
}
