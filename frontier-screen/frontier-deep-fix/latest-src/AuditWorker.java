public final class AuditWorker {
    private final ProductRepository repo;
    private final AuditSink sink;

    public AuditWorker(ProductRepository repo, AuditSink sink) {
        this.repo = repo;
        this.sink = sink;
    }

    public void deliver(AuditWork work) {
        // A work item is an immutable snapshot of the accepted write. Looking up the
        // current row here can report a later price (or fail after product deletion).
        java.math.BigDecimal price = work.price();
        if (price == null) {
            ProductSnapshot snapshot = repo.find(work.productId());
            price = snapshot.price();
        }
        sink.send("product:" + work.productId() + ":version:" + work.version(),
                  work.productId(), work.version(), price);
    }
}
