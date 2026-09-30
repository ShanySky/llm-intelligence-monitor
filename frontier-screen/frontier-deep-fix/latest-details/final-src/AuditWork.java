import java.math.BigDecimal;

public final class AuditWork {
    private final long productId;
    private final long version;
    private final BigDecimal price;

    public AuditWork(long productId, long version) {
        this(productId, version, null);
    }

    public AuditWork(long productId, long version, BigDecimal price) {
        this.productId = productId;
        this.version = version;
        this.price = price;
    }

    public long productId() { return productId; }
    public long version() { return version; }
    public BigDecimal price() { return price; }
}
