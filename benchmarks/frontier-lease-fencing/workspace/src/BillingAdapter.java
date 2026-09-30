import java.util.*;

public final class BillingAdapter {
    private final Set<String> acceptedKeys = new HashSet<>();
    private int effects;

    public synchronized void apply(String idempotencyKey) {
        if (acceptedKeys.add(idempotencyKey)) {
            effects += 1;
        }
    }

    public synchronized int effectCount() {
        return effects;
    }
}
