import java.util.*;

public final class PaymentProvider {
    private final Set<String> acceptedKeys = new HashSet<>();
    private int effects = 0;

    public synchronized void charge(String idempotencyKey, String orderId, long version) {
        if (acceptedKeys.add(idempotencyKey)) effects++;
    }

    public synchronized int effects() { return effects; }
}
