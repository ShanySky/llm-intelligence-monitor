public class PriceService {
    private final ProductRepository repo;
    private final ProductCache cache;
    private final AuditService audit;

    public PriceService(ProductRepository repo, ProductCache cache, AuditService audit) {
        this.repo = repo;
        this.cache = cache;
        this.audit = audit;
    }

    @Transactional
    public void changePrice(long id, BigDecimal price) {
        Product p = repo.findById(id).orElseThrow();
        p.setPrice(price);
        cache.evict(id);
        this.auditAsync(id, price);
    }

    @Async
    public void auditAsync(long id, BigDecimal price) {
        audit.sendPriceChanged(id, price);
    }
}
