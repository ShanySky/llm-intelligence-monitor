public final class AuditWorker {
  public void deliver(AuditWork work) {
    sink.send(work.auditKey(),work.productId(),work.version(),work.price());
  }
}
