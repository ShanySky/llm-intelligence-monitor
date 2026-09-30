import java.util.List;

public final class Page {
    public final List<FeedItem> items;
    public final String nextToken;

    public Page(List<FeedItem> items, String nextToken) {
        this.items = items;
        this.nextToken = nextToken;
    }
}
