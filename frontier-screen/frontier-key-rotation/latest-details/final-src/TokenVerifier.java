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
            // Tokens from the previous release did not identify a key. Try only
            // keys retained by this token's issuer during the overlap window.
            for (KeyVersion key : registry.all(p.issuer)) {
                if (codec.matches(p, key.secret)) return true;
            }
            return false;
        }

        long revision = registry.revision(p.issuer);
        KeyVersion key = cache.getOrLoad(
            p.issuer,
            revision,
            p.kid,
            () -> registry.byKid(p.issuer, p.kid)
        );
        // A supplied kid is authoritative. Never downgrade to another key.
        return key != null && codec.matches(p, key.secret);
    }
}
