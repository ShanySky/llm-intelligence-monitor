import java.util.*;

public final class FulfillmentRepository {
    private final Map<String,Fulfillment> rows = new HashMap<>();

    public synchronized Fulfillment findOrCreate(
        String eventId, String orderId, long version, String lineItemId
    ) {
        return rows.computeIfAbsent(
            eventId,
            k -> new Fulfillment(eventId, orderId, version, lineItemId)
        );
    }

    public synchronized int size() {
        return rows.size();
    }
}
