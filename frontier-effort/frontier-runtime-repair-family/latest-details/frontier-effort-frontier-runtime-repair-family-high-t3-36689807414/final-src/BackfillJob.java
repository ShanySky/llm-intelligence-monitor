public final class BackfillJob {
    private final CustomerStore store;
    public BackfillJob(CustomerStore store){ this.store=store; }

    public void apply(BackfillItem captured) {
        synchronized (store) {
            Customer current=store.get(captured.id());
            // A captured snapshot may be applied to its own version, or supersede
            // an older one, but must not roll back a later live write.
            if (captured.capturedVersion() >= current.version) {
                current.newStatus=captured.legacyStatus();
                current.version=captured.capturedVersion();
            }
        }
    }
}
