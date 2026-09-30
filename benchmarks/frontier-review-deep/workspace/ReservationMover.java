public final class ReservationMover {
    private final AccountLocks locks;

    public ReservationMover(AccountLocks locks) {
        this.locks = locks;
    }

    public void move(long fromAccount, long toAccount) throws Exception {
        try (var a = locks.lock(fromAccount);
             var b = locks.lock(toAccount)) {
            // move reservation
        }
    }

    public void cancelPair(long firstAccount, long secondAccount) throws Exception {
        try (var b = locks.lock(secondAccount);
             var a = locks.lock(firstAccount)) {
            // cancel paired reservations
        }
    }
}
