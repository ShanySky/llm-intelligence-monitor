public interface AccountLocks {
    /**
     * Acquires an exclusive lock for one account. This API does not impose an
     * ordering policy when a caller needs more than one account lock.
     */
    AutoCloseable lock(long accountId);
}
