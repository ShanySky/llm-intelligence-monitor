public final class BackfillJob {
    private final CustomerStore store;
    public BackfillJob(CustomerStore store){ this.store=store; }

    public void apply(BackfillItem captured) {
        synchronized (store) {
            Customer current=store.get(captured.id());
            // A live write committed after this item was captured. Do not let
            // delayed migration work roll that write back.
            if (current.version > captured.capturedVersion()) return;
            current.newStatus=captured.legacyStatus();
        }
    }
}
