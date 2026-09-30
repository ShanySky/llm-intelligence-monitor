import java.util.*;
import java.util.function.Function;

public final class Database {
    private Map<String, Order> orders = new HashMap<>();
    private Map<String, OutboxRecord> outbox = new LinkedHashMap<>();

    public synchronized void createOrder(String id, String orderKey) {
        orders.put(id, new Order(id, orderKey));
    }

    public synchronized Order getOrder(String id) {
        Order o = orders.get(id);
        return o == null ? null : o.copy();
    }

    public synchronized void saveOrder(Order order) {
        orders.put(order.id, order.copy());
    }

    public synchronized void saveOutbox(OutboxRecord record) {
        outbox.put(record.eventId, record.copy());
    }

    public synchronized int outboxSize() {
        return outbox.size();
    }

    public synchronized List<OutboxRecord> pendingOutbox() {
        List<OutboxRecord> rows = new ArrayList<>();
        for (OutboxRecord r : outbox.values()) {
            if (!r.sent) rows.add(r.copy());
        }
        return rows;
    }

    public synchronized void markSent(String eventId) {
        OutboxRecord r = outbox.get(eventId);
        if (r != null) r.sent = true;
    }

    public synchronized <T> T transaction(Function<Tx,T> body) {
        Map<String, Order> nextOrders = copyOrders(orders);
        Map<String, OutboxRecord> nextOutbox = copyOutbox(outbox);
        Tx tx = new Tx(nextOrders, nextOutbox);
        T result = body.apply(tx);
        orders = nextOrders;
        outbox = nextOutbox;
        return result;
    }

    private static Map<String, Order> copyOrders(Map<String, Order> src) {
        Map<String, Order> dst = new HashMap<>();
        for (var e : src.entrySet()) dst.put(e.getKey(), e.getValue().copy());
        return dst;
    }

    private static Map<String, OutboxRecord> copyOutbox(Map<String, OutboxRecord> src) {
        Map<String, OutboxRecord> dst = new LinkedHashMap<>();
        for (var e : src.entrySet()) dst.put(e.getKey(), e.getValue().copy());
        return dst;
    }

    public static final class Tx {
        private final Map<String, Order> orders;
        private final Map<String, OutboxRecord> outbox;

        Tx(Map<String, Order> orders, Map<String, OutboxRecord> outbox) {
            this.orders = orders;
            this.outbox = outbox;
        }

        public Order getOrder(String id) {
            return orders.get(id);
        }

        public void saveOrder(Order order) {
            orders.put(order.id, order);
        }

        public OutboxRecord getOutbox(String eventId) {
            return outbox.get(eventId);
        }

        public void saveOutboxIfAbsent(OutboxRecord record) {
            outbox.putIfAbsent(record.eventId, record);
        }
    }
}
