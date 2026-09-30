public final class AuditWorker {
    private final ProductRepository repo;
    private final AuditSink sink;

    public AuditWorker(ProductRepository repo, AuditSink sink) {
        this.repo = repo;
        this.sink = sink;
    }

    public void deliver(AuditWork work) {
        ProductSnapshot current = repo.find(work.productId());
        sink.send(
            UUID.randomUUID().toString(),
            work.productId(),
            work.version(),
            current.price()
        );
    }
}
