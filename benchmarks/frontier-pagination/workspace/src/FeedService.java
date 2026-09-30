import java.util.List;

public final class FeedService {
    private final FeedStore store;
    private final CursorCodec codec;

    public FeedService(FeedStore store, CursorCodec codec) {
        this.store = store;
        this.codec = codec;
    }

    public Page page(String token, int limit) {
        if (limit < 1 || limit > 100) {
            throw new IllegalArgumentException("limit");
        }

        long currentSnapshot = store.snapshot();
        Cursor cursor = codec.decode(token, currentSnapshot);
        List<FeedItem> items = store.page(
            currentSnapshot,
            cursor.createdAt,
            cursor.id,
            limit
        );

        String next = items.size() < limit
            ? null
            : codec.encode(currentSnapshot, items.get(items.size() - 1));

        return new Page(items, next);
    }
}
