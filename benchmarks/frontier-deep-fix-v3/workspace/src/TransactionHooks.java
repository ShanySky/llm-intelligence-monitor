import java.util.*;

public final class TransactionHooks {
    private static final ThreadLocal<List<Runnable>> AFTER = new ThreadLocal<>();

    private TransactionHooks() {}

    public static void afterCommit(Runnable action) {
        List<Runnable> pending = AFTER.get();
        if (pending == null) {
            action.run();
        } else {
            pending.add(action);
        }
    }

    public static boolean active() {
        return AFTER.get() != null;
    }

    public static void runInTransaction(Runnable body) {
        if (AFTER.get() != null) {
            body.run();
            return;
        }
        List<Runnable> pending = new ArrayList<>();
        AFTER.set(pending);
        try {
            body.run();
        } catch (RuntimeException | Error e) {
            AFTER.remove();
            throw e;
        }
        AFTER.remove();
        for (Runnable action : pending) action.run();
    }
}
