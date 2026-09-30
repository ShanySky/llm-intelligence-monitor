public final class AuditWorker {
    private final ProductRepository repo;
    private final AuditSink sink;

    public AuditWorker(ProductRepository repo, AuditSink sink) {
        this.repo = repo;
        this.sink = sink;
    }

    public void deliver(AuditWork work) {
        ProductSnapshot current = work.price() == null ? repo.find(work.productId()) : null;
        sink.send(
            "product:" + work.productId() + ":version:" + work.version(),
            work.productId(),
            work.version(),
            work.price() == null ? current.price() : work.price()
        );
    }
}
