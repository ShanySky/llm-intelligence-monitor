public final class SessionService {
  private final SessionStore store;

  public Session refresh(String sessionId, String newJwt) {
    Session old = store.get(sessionId);
    Session replacement = new Session(sessionId, newJwt, UUID.randomUUID().toString());
    store.save(replacement);
    return replacement;
  }
}
