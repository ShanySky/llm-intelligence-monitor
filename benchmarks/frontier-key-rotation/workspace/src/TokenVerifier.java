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
        KeyVersion key;
        if (p.kid == null) {
            key = registry.active(p.issuer);
        } else {
            long revision = registry.revision(p.issuer);
            key = cache.getOrLoad(
                p.issuer,
                revision,
                p.kid,
                () -> registry.byKid(p.issuer, p.kid)
            );
            if (key == null) {
                key = registry.active(p.issuer);
            }
        }
        return key != null && codec.matches(p, key.secret);
    }
}
