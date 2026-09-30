public interface ProductCache {
    /**
     * Evicts the currently published cache entry. Cache-aside readers may
     * repopulate an entry from repository state after an eviction.
     */
    void evict(long productId);
}
