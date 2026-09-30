public final class RolloutProbe {
    public static void main(String[] args) {
        legacyOverlap();
        unknownKidMustNotFallback();
        issuerScopedCache();
        removedKeyMustStopWorking();
        System.out.println("ROLLOUT_PROBE_PASS");
    }

    static void legacyOverlap() {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "k1", "old", false);
        registry.addKey("issuer-a", "k2", "new", true);
        TokenCodec codec = new TokenCodec();
        TokenVerifier verifier = new TokenVerifier(registry, new KeyCache(), codec);

        String legacy = codec.encode("issuer-a", null, "user-1", "old");
        check(verifier.verify(legacy), "legacy session signed by retained previous key");
    }

    static void unknownKidMustNotFallback() {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "k2", "new", true);
        TokenCodec codec = new TokenCodec();
        TokenVerifier verifier = new TokenVerifier(registry, new KeyCache(), codec);

        String forged = codec.encode("issuer-a", "unknown", "user-1", "new");
        check(!verifier.verify(forged), "unknown kid must not fall back to active key");
    }

    static void issuerScopedCache() {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "shared", "secret-a", true);
        registry.addKey("issuer-b", "shared", "secret-b", true);
        TokenCodec codec = new TokenCodec();
        KeyCache cache = new KeyCache();
        TokenVerifier verifier = new TokenVerifier(registry, cache, codec);

        String a = codec.encode("issuer-a", "shared", "alice", "secret-a");
        String b = codec.encode("issuer-b", "shared", "bob", "secret-b");
        check(verifier.verify(a), "issuer-a token");
        check(verifier.verify(b), "issuer-b token with same kid");
    }

    static void removedKeyMustStopWorking() {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "k1", "old", false);
        registry.addKey("issuer-a", "k2", "new", true);
        TokenCodec codec = new TokenCodec();
        KeyCache cache = new KeyCache();
        TokenVerifier verifier = new TokenVerifier(registry, cache, codec);

        String old = codec.encode("issuer-a", "k1", "user-1", "old");
        check(verifier.verify(old), "old keyed token while retained");
        registry.removeKey("issuer-a", "k1");
        check(!verifier.verify(old), "removed key must invalidate cached verification");
    }

    static void check(boolean ok, String name) {
        if (!ok) throw new AssertionError(name);
    }
}
