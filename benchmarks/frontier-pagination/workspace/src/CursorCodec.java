public final class CursorCodec {
    public String encode(long snapshot, FeedItem last) {
        return "v1:" + last.createdAt;
    }

    public Cursor decode(String token, long currentSnapshot) {
        if (token == null || token.isBlank()) {
            return new Cursor(currentSnapshot, Long.MAX_VALUE, Long.MAX_VALUE, false);
        }
        if (!token.startsWith("v1:")) {
            throw new IllegalArgumentException("unsupported cursor");
        }
        try {
            long createdAt = Long.parseLong(token.substring(3));
            return new Cursor(currentSnapshot, createdAt, Long.MAX_VALUE, true);
        } catch (RuntimeException e) {
            throw new IllegalArgumentException("invalid cursor", e);
        }
    }
}
