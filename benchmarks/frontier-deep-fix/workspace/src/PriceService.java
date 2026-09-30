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
        repo.updateIfVersion(id, expectedVersion, newPrice);
        cache.evict(id);
        audits.enqueue(new AuditWork(id, expectedVersion + 1));
    }
}
