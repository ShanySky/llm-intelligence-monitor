public interface ProductRepository {
    ProductSnapshot find(long id);
    boolean updateIfVersion(long id, long expectedVersion, BigDecimal newPrice);
}
