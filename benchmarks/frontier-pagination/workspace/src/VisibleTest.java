public final class VisibleTest {
    public static void main(String[] args) {
        FeedStore store = new FeedStore();
        store.add(1, 300, "a");
        store.add(2, 200, "b");
        store.add(3, 100, "c");

        FeedService service = new FeedService(store, new CursorCodec());
        Page first = service.page(null, 2);
        check(first.items.size() == 2);
        check(first.items.get(0).id == 1);
        check(first.items.get(1).id == 2);
        check(first.nextToken != null);

        Page second = service.page(first.nextToken, 2);
        check(second.items.size() == 1);
        check(second.items.get(0).id == 3);
        check(second.nextToken == null);

        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
