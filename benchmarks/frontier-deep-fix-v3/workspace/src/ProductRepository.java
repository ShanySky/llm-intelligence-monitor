import java.math.BigDecimal;

public interface ProductRepository {
    ProductSnapshot find(long id);

    /**
     * Attempts one optimistic write. Returns true only when the expected version
     * matched and the new version became the repository's committed value.
     * A false result leaves repository state unchanged.
     */
    boolean updateIfVersion(long id, long expectedVersion, BigDecimal newPrice);
}
