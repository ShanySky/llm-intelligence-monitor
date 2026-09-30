public final class VisibleTest {
    public static void main(String[] args) {
        KeyRegistry registry = new KeyRegistry();
        registry.addKey("issuer-a", "k2", "secret-new", true);

        TokenCodec codec = new TokenCodec();
        TokenSigner signer = new TokenSigner(registry, codec);
        TokenVerifier verifier = new TokenVerifier(registry, new KeyCache(), codec);

        String token = signer.issue("issuer-a", "user-1");
        if (!verifier.verify(token)) throw new AssertionError("new token must verify");

        System.out.println("VISIBLE_TEST_PASS");
    }
}
