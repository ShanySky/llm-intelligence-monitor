public final class BackfillJob {
    private final OrderStore store;

    public BackfillJob(OrderStore store) {
        this.store = store;
    }

    public BackfillItem plan(String id) {
        OrderRecord row = store.get(id);
        if (row == null) {
            return null;
        }
        synchronized (row) {
            if (row.legacyStatus == null) {
                return null;
            }
            return new BackfillItem(id, row.legacyStatus, row.legacyVersion);
        }
    }

    public void apply(BackfillItem item) {
        if (item == null) {
            return;
        }
        OrderRecord row = store.get(item.id());
        if (row == null) {
            return;
        }
        synchronized (row) {
            if (row.legacyVersion != item.sourceVersion()
                    || !item.legacyStatus().equals(row.legacyStatus)
                    || row.newVersion >= item.sourceVersion()) {
                return;
            }
            row.statusCode = StatusCodec.toCode(item.legacyStatus());
            row.statusReason = "backfill";
            row.newVersion = item.sourceVersion();
        }
    }
}
