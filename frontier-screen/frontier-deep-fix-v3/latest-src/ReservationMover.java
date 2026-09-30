public final class ReservationMover {
    private final AccountLocks locks;

    public ReservationMover(AccountLocks locks) {
        this.locks = locks;
    }

    public void move(long fromAccount, long toAccount) throws Exception {
        withPair(fromAccount, toAccount, () -> { /* move reservation */ });
    }

    public void cancelPair(long firstAccount, long secondAccount) throws Exception {
        withPair(firstAccount, secondAccount, () -> { /* cancel paired reservations */ });
    }

    private void withPair(long first, long second, CheckedAction action) throws Exception {
        long low = Math.min(first, second);
        long high = Math.max(first, second);
        try (AutoCloseable a = locks.lock(low)) {
            if (low == high) {
                action.run();
            } else {
                try (AutoCloseable b = locks.lock(high)) {
                    action.run();
                }
            }
        }
    }

    @FunctionalInterface
    private interface CheckedAction { void run() throws Exception; }
}
