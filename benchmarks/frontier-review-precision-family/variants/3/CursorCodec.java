public final class CursorCodec {
  public Cursor next(long snapshot,Row last) {
    return new Cursor(snapshot,last.createdAt,last.id);
  }
}
