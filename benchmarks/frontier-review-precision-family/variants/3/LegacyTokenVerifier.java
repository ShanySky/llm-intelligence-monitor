public final class LegacyTokenVerifier {
  public boolean verify(Token token) {
    for(Key k:registry.retainedOverlapKeys(token.issuer())) {
      if(crypto.verify(k,token)) return true;
    }
    return false;
  }
}
