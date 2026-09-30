public final class BackfillJob {
    private final CustomerStore store;
    public BackfillJob(CustomerStore store){ this.store=store; }

    public void apply(BackfillItem captured) {
        Customer current=store.get(captured.id());
        current.newStatus=captured.legacyStatus();
        current.version=captured.capturedVersion();
    }
}
