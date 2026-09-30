public final class FeedItem {
    final long id;
    final long createdAt;
    final long sequence;
    final String value;

    FeedItem(long id, long createdAt, long sequence, String value) {
        this.id = id;
        this.createdAt = createdAt;
        this.sequence = sequence;
        this.value = value;
    }
}
