import java.util.*;

public final class EventBroker {
    private final Set<String> deliveredKeys = new HashSet<>();
    private final List<String> payloads = new ArrayList<>();

    public synchronized void publish(String idempotencyKey, String payload) {
        if (deliveredKeys.add(idempotencyKey)) {
            payloads.add(payload);
        }
    }

    public synchronized int deliveredCount() {
        return payloads.size();
    }

    public synchronized List<String> payloads() {
        return List.copyOf(payloads);
    }
}
