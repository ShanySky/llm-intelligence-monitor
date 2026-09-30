public final class V1OrderService {
    private final OrderStore store;

    public V1OrderService(OrderStore store) {
        this.store = store;
    }

    public void writeStatus(String id, String status) {
        OrderRecord row = store.getOrCreate(id);
        synchronized (row) {
            long v = row.nextVersion();
            row.legacyStatus = status;
            row.legacyVersion = v;
        }
    }

    public String readStatus(String id) {
        OrderRecord row = store.get(id);
        return row == null ? null : row.legacyStatus;
    }
}
