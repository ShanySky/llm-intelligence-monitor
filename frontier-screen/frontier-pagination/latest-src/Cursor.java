public final class Cursor {
    final long snapshot;
    final long createdAt;
    final long id;
    final boolean legacy;

    Cursor(long snapshot, long createdAt, long id, boolean legacy) {
        this.snapshot = snapshot;
        this.createdAt = createdAt;
        this.id = id;
        this.legacy = legacy;
    }
}
