
public final class AuditWorker {
    private final ProductRepository repo;
    private final AuditSink sink;

    public AuditWorker(ProductRepository repo, AuditSink sink) {
        this.repo = repo;
        this.sink = sink;
    }

    public void deliver(AuditWork work) {
        // AuditWork carries the accepted value: looking up the current row here
        // would report a later version when delivery is delayed.
        java.math.BigDecimal price = work.price();
        if (price == null) price = repo.find(work.productId()).price();
        sink.send("product:" + work.productId() + ":version:" + work.version(),
            work.productId(), work.version(), price);
    }
}
