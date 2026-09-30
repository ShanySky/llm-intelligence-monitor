public final class TokenSigner {
    private final KeyRegistry registry;
    private final TokenCodec codec;

    public TokenSigner(KeyRegistry registry, TokenCodec codec) {
        this.registry = registry;
        this.codec = codec;
    }

    public String issue(String issuer, String subject) {
        KeyVersion key = registry.active(issuer);
        if (key == null) throw new IllegalArgumentException("no active key");
        return codec.encode(issuer, key.kid, subject, key.secret);
    }
}
