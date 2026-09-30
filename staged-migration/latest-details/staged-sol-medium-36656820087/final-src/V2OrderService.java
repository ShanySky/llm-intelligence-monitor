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
            row.legacyStatus = status;
            row.legacyVersion = v;
            row.statusCode = code;
            row.statusReason = reason;
            row.newVersion = v;
        }
    }

    public String readStatus(String id) {
        OrderRecord row = store.get(id);
        if (row == null) {
            return null;
        }
        synchronized (row) {
            if (row.statusCode == null || row.legacyVersion > row.newVersion) {
                return row.legacyStatus;
            }
            return StatusCodec.fromCode(row.statusCode);
        }
    }
}
