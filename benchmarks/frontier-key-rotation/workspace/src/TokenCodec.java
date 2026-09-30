public final class TokenCodec {
    public String encode(String issuer, String kid, String subject, String secret) {
        String actualKid = kid == null ? "-" : kid;
        return issuer + ";" + actualKid + ";" + subject + ";" + sign(issuer, subject, secret);
    }

    public Parts decode(String token) {
        String[] p = token.split(";", -1);
        if (p.length != 4 || p[0].isBlank() || p[2].isBlank()) {
            throw new IllegalArgumentException("invalid token");
        }
        return new Parts(p[0], "-".equals(p[1]) ? null : p[1], p[2], p[3]);
    }

    public boolean matches(Parts token, String secret) {
        return sign(token.issuer, token.subject, secret).equals(token.signature);
    }

    private String sign(String issuer, String subject, String secret) {
        return secret + "#" + issuer + "#" + subject;
    }

    public static final class Parts {
        final String issuer;
        final String kid;
        final String subject;
        final String signature;

        Parts(String issuer, String kid, String subject, String signature) {
            this.issuer = issuer;
            this.kid = kid;
            this.subject = subject;
            this.signature = signature;
        }
    }
}
