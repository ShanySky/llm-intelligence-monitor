import java.util.*;

public final class InventoryClient {
    private final Set<String> accepted = new HashSet<>();

    public synchronized String reserve(String idempotencyKey) {
        accepted.add(idempotencyKey);
        return "reservation:" + idempotencyKey;
    }

    public synchronized int effectCount() {
        return accepted.size();
    }
}
