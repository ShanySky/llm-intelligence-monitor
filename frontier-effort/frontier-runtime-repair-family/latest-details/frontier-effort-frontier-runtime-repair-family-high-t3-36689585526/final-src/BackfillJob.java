public final class BackfillJob {
    private final CustomerStore store;
    public BackfillJob(CustomerStore store){ this.store=store; }

    public void apply(BackfillItem captured) {
        store.applyBackfill(captured);
    }
}
