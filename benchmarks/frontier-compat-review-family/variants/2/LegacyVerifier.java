public final class LegacyVerifier {
  public boolean verify(Token token) {
    if (token.kid() != null) return verifyKey(token.issuer(), token.kid(), token);
    for (Key key : registry.allRetainedOverlapKeys()) {
      if (verify(key, token)) return true;
    }
    return false;
  }
}
