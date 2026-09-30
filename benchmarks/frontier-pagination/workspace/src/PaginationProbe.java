import java.util.*;

public final class PaginationProbe {
    public static void main(String[] args) {
        tieBoundary();
        writeBetweenPages();
    }

    static void tieBoundary() {
        FeedStore store = new FeedStore();
        store.add(10, 300, "a");
        store.add(9, 200, "b");
        store.add(8, 200, "c");
        store.add(7, 200, "d");
        store.add(6, 100, "e");

        FeedService service = new FeedService(store, new CursorCodec());
        Page p1 = service.page(null, 2);
        Page p2 = service.page(p1.nextToken, 2);

        Set<Long> ids = new LinkedHashSet<>();
        for (FeedItem x : p1.items) ids.add(x.id);
        for (FeedItem x : p2.items) ids.add(x.id);

        if (ids.size() != 4 || !ids.containsAll(List.of(10L,9L,8L,7L))) {
            throw new AssertionError("tie boundary lost or duplicated rows: " + ids);
        }
    }

    static void writeBetweenPages() {
        FeedStore store = new FeedStore();
        store.add(5, 500, "a");
        store.add(4, 400, "b");
        store.add(3, 300, "c");
        store.add(2, 200, "d");
        store.add(1, 100, "e");

        FeedService service = new FeedService(store, new CursorCodec());
        Page p1 = service.page(null, 2);
        store.add(99, 350, "new-after-page-one");
        Page p2 = service.page(p1.nextToken, 2);

        for (FeedItem x : p2.items) {
            if (x.id == 99) throw new AssertionError("post-snapshot insert leaked into resumed page");
        }
    }
}
