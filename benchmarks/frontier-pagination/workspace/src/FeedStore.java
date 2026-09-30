import java.util.*;

public final class FeedStore {
    private final List<FeedItem> items = new ArrayList<>();
    private long sequence = 0;

    public synchronized FeedItem add(long id, long createdAt, String value) {
        FeedItem item = new FeedItem(id, createdAt, ++sequence, value);
        items.add(item);
        return item;
    }

    public synchronized long snapshot() {
        return sequence;
    }

    public synchronized List<FeedItem> page(long snapshot, long beforeCreatedAt, long beforeId, int limit) {
        return items.stream()
            .filter(x -> x.createdAt < beforeCreatedAt)
            .sorted(Comparator.comparingLong((FeedItem x) -> x.createdAt).reversed())
            .limit(limit)
            .toList();
    }
}
