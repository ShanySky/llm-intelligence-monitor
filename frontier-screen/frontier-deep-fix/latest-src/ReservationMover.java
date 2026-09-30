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
        // Avoid acquiring a non-reentrant lock twice for a same-account pair.
        try (var a = locks.lock(low)) {
            if (low == high) {
                // operation is intentionally within the one acquired account lock
                return;
            }
            try (var b = locks.lock(high)) {
                // move/cancel operation runs while both canonical locks are held
            }
        }
    }
}
