import java.math.BigDecimal;

public interface AuditSink {
    /**
     * The sink deduplicates retries only when callers reuse the same
     * idempotencyKey. Different keys are independent logical deliveries.
     */
    void send(String idempotencyKey, long productId, long version, BigDecimal price);
}
