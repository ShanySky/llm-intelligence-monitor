public class AuditService {
    private final AuditSink sink;
    private final ProductRepository repo;

    public AuditService(AuditSink sink, ProductRepository repo) {
        this.sink = sink;
        this.repo = repo;
    }

    public void sendPriceChanged(long id, BigDecimal expectedPrice) {
        Product current = repo.findById(id).orElseThrow();
        String idempotencyKey = UUID.randomUUID().toString();
        sink.send(idempotencyKey, id, current.getPrice(), expectedPrice);
    }
}
