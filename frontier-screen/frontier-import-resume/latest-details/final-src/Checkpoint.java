public final class Checkpoint {
    int offset;
    long snapshot = -1;
    long beforeCreatedAt = Long.MAX_VALUE;
    long beforeId = Long.MAX_VALUE;
    long beforeIngestSeq = Long.MAX_VALUE;

    Checkpoint copy() {
        Checkpoint c = new Checkpoint();
        c.offset = offset;
        c.snapshot = snapshot;
        c.beforeCreatedAt = beforeCreatedAt;
        c.beforeId = beforeId;
        c.beforeIngestSeq = beforeIngestSeq;
        return c;
    }
}
