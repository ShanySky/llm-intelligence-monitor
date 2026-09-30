public final class V2OrderService {
    private final OrderStore store;

    public V2OrderService(OrderStore store) {
        this.store = store;
    }

    public void writeStatus(String id, String status, String reason) {
        OrderRecord row = store.getOrCreate(id);
        synchronized (row) {
            int code = StatusCodec.toCode(status);
            long v = row.nextVersion();
            row.statusCode = code;
            row.statusReason = reason;
            row.newVersion = v;
            row.legacyStatus = status;
            row.legacyVersion = v;
        }
    }

    public String readStatus(String id) {
        OrderRecord row = store.get(id);
        if (row == null) {
            return null;
        }
        synchronized (row) {
            if (row.legacyVersion > row.newVersion || row.statusCode == null) {
                return row.legacyStatus;
            }
            return StatusCodec.fromCode(row.statusCode);
        }
    }
}
