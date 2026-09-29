import java.util.*;

public final class InventoryClient {
    private final Map<String, String> reservations = new HashMap<>();

    public synchronized String reserve(String orderId, String idempotencyKey) {
        reservations.putIfAbsent(idempotencyKey, orderId);
        return idempotencyKey;
    }

    public synchronized void release(String idempotencyKey) {
        reservations.remove(idempotencyKey);
    }

    public synchronized boolean has(String idempotencyKey) {
        return reservations.containsKey(idempotencyKey);
    }

    public synchronized int reservationCount() {
        return reservations.size();
    }
}
