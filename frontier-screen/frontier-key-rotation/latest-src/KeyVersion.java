public final class KeyVersion {
    final String issuer;
    final String kid;
    final String secret;
    final boolean active;

    KeyVersion(String issuer, String kid, String secret, boolean active) {
        this.issuer = issuer;
        this.kid = kid;
        this.secret = secret;
        this.active = active;
    }
}
