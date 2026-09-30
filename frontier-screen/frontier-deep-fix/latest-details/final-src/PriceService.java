import java.math.BigDecimal;

public final class PriceService {
    private final ProductRepository repo;
    private final ProductCache cache;
    private final AuditQueue audits;

    public PriceService(ProductRepository repo, ProductCache cache, AuditQueue audits) {
        this.repo = repo;
        this.cache = cache;
        this.audits = audits;
    }

    @Transactional
    public void changePrice(long id, long expectedVersion, BigDecimal newPrice) {
        if (!repo.updateIfVersion(id, expectedVersion, newPrice)) return;
        long version = expectedVersion + 1;
        // A cache miss may repopulate from the still-committed old row while the
        // transaction is open. Evict only after commit, so that value cannot survive.
        TransactionHooks.afterCommit(() -> cache.evict(id));
        TransactionHooks.afterCommit(() -> audits.enqueue(new AuditWork(id, version, newPrice)));
    }
}
