public interface AuditSink {
    void send(String idempotencyKey, long productId, long version, BigDecimal price);
}
