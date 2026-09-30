public final class ImportRow {
    final long id;
    final long createdAt;
    final long ingestSeq;
    final String value;

    ImportRow(long id, long createdAt, long ingestSeq, String value) {
        this.id = id;
        this.createdAt = createdAt;
        this.ingestSeq = ingestSeq;
        this.value = value;
    }
}
