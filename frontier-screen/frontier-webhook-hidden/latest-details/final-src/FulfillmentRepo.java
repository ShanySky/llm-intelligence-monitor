import java.util.*;

public final class FulfillmentRepo {
    private final Map<String, Fulfillment> rows = new HashMap<>();

    public synchronized Fulfillment getOrCreate(String key, String orderId) {
        return rows.computeIfAbsent(key, k -> new Fulfillment(orderId));
    }

    public synchronized Fulfillment get(String key) {
        return rows.get(key);
    }
}
