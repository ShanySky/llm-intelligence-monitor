import java.util.*;

public final class CustomerApi {
    private final Map<String, Long> effects = new HashMap<>();
    private final Set<Long> rows = new HashSet<>();

    public synchronized void upsert(long rowId, String idempotencyKey, String value) {
        Long existing = effects.get(idempotencyKey);
        if (existing != null) {
            if (existing.longValue() != rowId) {
                throw new IllegalStateException("idempotency key collision");
            }
            return;
        }
        effects.put(idempotencyKey, rowId);
        rows.add(rowId);
    }

    public synchronized int effectCount() {
        return effects.size();
    }

    public synchronized boolean hasRow(long rowId) {
        return rows.contains(rowId);
    }
}
