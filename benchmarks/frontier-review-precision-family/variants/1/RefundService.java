public final class RefundService {
  @Transactional
  public void refund(String refundId,String paymentId,Money amount) {
    Refund row=refunds.getOrCreate(refundId);
    if(row.completed) return;
    provider.refund(paymentId,UUID.randomUUID().toString(),amount);
    failure.afterProviderAccepted(refundId);
    row.completed=true;
  }
}
