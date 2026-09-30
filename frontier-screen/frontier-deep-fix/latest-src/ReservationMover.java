public final class ReservationMover {
    private final AccountLocks locks;

    public ReservationMover(AccountLocks locks) {
        this.locks = locks;
    }

    public void move(long fromAccount, long toAccount) throws Exception {
        withPair(fromAccount, toAccount);
    }

    public void cancelPair(long firstAccount, long secondAccount) throws Exception {
        withPair(firstAccount, secondAccount);
    }

    private void withPair(long first, long second) throws Exception {
        long low = Math.min(first, second);
        long high = Math.max(first, second);
        if (low == high) {
            try (AutoCloseable ignored = locks.lock(low)) { /* operation */ }
        } else {
            try (AutoCloseable a = locks.lock(low);
                 AutoCloseable b = locks.lock(high)) { /* operation */ }
        }
    }
}
