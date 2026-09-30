public final class RolloutProbe {
    public static void main(String[] args) {
        legacyOverlap();
        unknownKidMustNotFallback();
        issuerScopedCache();
        removedKeyMustStopWorking();
        replacedKeyMustInvalidateCache();
        legacyKeyRemovalAndIssuerIsolation();
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

    static void replacedKeyMustInvalidateCache() {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "shared", "old", true);
        TokenCodec codec = new TokenCodec();
        TokenVerifier verifier = new TokenVerifier(registry, new KeyCache(), codec);
        String old = codec.encode("issuer-a", "shared", "user", "old");
        check(verifier.verify(old), "warm old key");
        registry.addKey("issuer-a", "shared", "new", true);
        check(!verifier.verify(old), "replaced key must not remain cached");
        check(verifier.verify(codec.encode("issuer-a", "shared", "user", "new")),
              "new key with same kid must verify");
    }

    static void legacyKeyRemovalAndIssuerIsolation() {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "old", "retained", false);
        registry.addKey("issuer-a", "new", "current", true);
        registry.addKey("issuer-b", "other", "other-secret", true);
        TokenCodec codec = new TokenCodec();
        TokenVerifier verifier = new TokenVerifier(registry, new KeyCache(), codec);
        String legacy = codec.encode("issuer-a", null, "user", "retained");
        check(verifier.verify(legacy), "retained legacy key verifies");
        check(!verifier.verify(codec.encode("issuer-b", null, "user", "retained")),
              "legacy token cannot use another issuer's key");
        registry.removeKey("issuer-a", "old");
        check(!verifier.verify(legacy), "legacy token stops working after key removal");
    }

    static void check(boolean ok, String name) {
        if (!ok) throw new AssertionError(name);
    }
}
