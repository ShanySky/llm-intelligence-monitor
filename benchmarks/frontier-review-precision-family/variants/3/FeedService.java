public final class FeedService {
  public Page page(Cursor cursor,int limit) {
    long snapshot = store.currentSequence();
    return store.page(snapshot,cursor.createdAt(),cursor.id(),limit);
  }
}
