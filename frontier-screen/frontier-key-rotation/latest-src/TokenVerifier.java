public final class TokenVerifier {
    private final KeyRegistry registry;
    private final KeyCache cache;
    private final TokenCodec codec;

    public TokenVerifier(KeyRegistry registry, KeyCache cache, TokenCodec codec) {
        this.registry = registry;
        this.cache = cache;
        this.codec = codec;
    }

    public boolean verify(String token) {
        TokenCodec.Parts p = codec.decode(token);
        if (p.kid == null) {
            // Previous releases did not include a kid. Only retained keys for this
            // issuer may validate those sessions, including keys no longer active.
            for (KeyVersion key : registry.all(p.issuer)) {
                if (codec.matches(p, key.secret)) return true;
            }
            return false;
        }

        KeyVersion key = cache.getOrLoad(
            p.issuer,
            registry.revision(p.issuer),
            p.kid,
            () -> registry.byKid(p.issuer, p.kid)
        );
        // A supplied kid is authoritative: never try another key on a miss.
        return key != null && codec.matches(p, key.secret);
    }
}
