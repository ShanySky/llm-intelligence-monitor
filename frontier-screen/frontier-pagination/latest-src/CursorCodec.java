public final class CursorCodec {
    public String encode(long snapshot, FeedItem last) {
        return "v2:" + snapshot + ":" + last.createdAt + ":" + last.id;
    }

    public Cursor decode(String token, long currentSnapshot) {
        if (token == null || token.isBlank()) {
            return new Cursor(currentSnapshot, Long.MAX_VALUE, Long.MAX_VALUE, false);
        }
        try {
            if (token.startsWith("v1:")) {
                // Legacy links only recorded the timestamp. Treat that whole timestamp
                // bucket as consumed, matching the old strict-before resume behavior.
                long createdAt = Long.parseLong(token.substring(3));
                return new Cursor(currentSnapshot, createdAt, Long.MIN_VALUE, true);
            }
            if (token.startsWith("v2:")) {
                String[] parts = token.split(":", -1);
                if (parts.length != 4) throw new IllegalArgumentException("invalid cursor");
                return new Cursor(Long.parseLong(parts[1]), Long.parseLong(parts[2]),
                                  Long.parseLong(parts[3]), false);
            }
            throw new IllegalArgumentException("unsupported cursor");
        } catch (RuntimeException e) {
            if (e instanceof IllegalArgumentException && "unsupported cursor".equals(e.getMessage())) throw e;
            throw new IllegalArgumentException("invalid cursor", e);
        }
    }
}
