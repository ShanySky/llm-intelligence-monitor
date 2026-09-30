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
            row.statusCode = StatusCodec.toCode(status);
            row.statusReason = "legacy";
            row.newVersion = v;
        }
    }

    public String readStatus(String id) {
        OrderRecord row = store.get(id);
        if (row == null) {
            return null;
        }
        synchronized (row) {
            if (row.statusCode != null && row.newVersion >= row.legacyVersion) {
                return StatusCodec.fromCode(row.statusCode);
            }
            return row.legacyStatus != null ? row.legacyStatus
                    : (row.statusCode == null ? null : StatusCodec.fromCode(row.statusCode));
        }
    }
}
