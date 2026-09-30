public interface AccountLocks {
    AutoCloseable lock(long accountId);
}
