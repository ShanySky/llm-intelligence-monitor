import java.util.*;

public final class KeyRegistry {
    private static final class State {
        final List<KeyVersion> keys = new ArrayList<>();
        long revision = 0;
    }

    private final Map<String, State> issuers = new HashMap<>();

    public synchronized void addKey(String issuer, String kid, String secret, boolean active) {
        State s = issuers.computeIfAbsent(issuer, x -> new State());
        if (active) {
            for (int i = 0; i < s.keys.size(); i++) {
                KeyVersion k = s.keys.get(i);
                if (k.active) s.keys.set(i, new KeyVersion(k.issuer, k.kid, k.secret, false));
            }
        }
        s.keys.removeIf(k -> k.kid.equals(kid));
        s.keys.add(new KeyVersion(issuer, kid, secret, active));
        s.revision++;
    }

    public synchronized void removeKey(String issuer, String kid) {
        State s = issuers.get(issuer);
        if (s == null) return;
        s.keys.removeIf(k -> k.kid.equals(kid));
        s.revision++;
    }

    public synchronized KeyVersion active(String issuer) {
        State s = issuers.get(issuer);
        if (s == null) return null;
        for (KeyVersion k : s.keys) if (k.active) return k;
        return null;
    }

    public synchronized KeyVersion byKid(String issuer, String kid) {
        State s = issuers.get(issuer);
        if (s == null) return null;
        for (KeyVersion k : s.keys) if (k.kid.equals(kid)) return k;
        return null;
    }

    public synchronized List<KeyVersion> all(String issuer) {
        State s = issuers.get(issuer);
        return s == null ? List.of() : List.copyOf(s.keys);
    }

    public synchronized long revision(String issuer) {
        State s = issuers.get(issuer);
        return s == null ? 0 : s.revision;
    }
}
