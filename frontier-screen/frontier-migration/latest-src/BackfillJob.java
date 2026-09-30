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
            return row.legacyStatus == null ? null
                    : new BackfillItem(id, row.legacyStatus, row.legacyVersion);
        }
    }

    public void apply(BackfillItem item) {
        if (item == null) {
            return;
        }
        OrderRecord row = store.getOrCreate(item.id());
        synchronized (row) {
            // Apply only if the snapshot still describes the current legacy value,
            // and no newer structured write has occurred since it was planned.
            if (row.legacyStatus != null
                    && row.legacyVersion == item.sourceVersion()
                    && row.legacyStatus.equals(item.legacyStatus())
                    && row.newVersion <= item.sourceVersion()) {
                row.statusCode = StatusCodec.toCode(item.legacyStatus());
                row.statusReason = "backfill";
                row.newVersion = item.sourceVersion();
            }
        }
    }
}
