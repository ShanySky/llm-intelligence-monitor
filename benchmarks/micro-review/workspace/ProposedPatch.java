// Proposed patch (simplified)
@Service
public class ProductService {
    private final ProductRepository repo;
    private final ProductCache cache;
    private final AuditClient auditClient;

    @Transactional
    public void changePrice(long id, BigDecimal newPrice) {
        Product p = repo.findById(id).orElseThrow();
        p.setPrice(newPrice);
        cache.evict(id);
        this.auditAsync(id, newPrice);
    }

    @Async
    public void auditAsync(long id, BigDecimal price) {
        Product p = repo.findById(id).orElseThrow();
        auditClient.send(new AuditEvent(UUID.randomUUID().toString(), p.getId(), price));
    }
}
