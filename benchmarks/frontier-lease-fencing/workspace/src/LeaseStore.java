import java.util.*;

public final class LeaseStore {
    private final Map<String, Lease> leases = new HashMap<>();
    private final Map<String, Long> lastToken = new HashMap<>();

    public synchronized Lease acquire(String jobId, String owner, long now, long ttl) {
        Lease current = leases.get(jobId);
        if (current != null && current.expiresAt > now) {
            return current;
        }

        long token = 1L;
        Lease next = new Lease(jobId, owner, token, now + ttl);
        leases.put(jobId, next);
        lastToken.put(jobId, token);
        return next;
    }

    public synchronized boolean renew(String jobId, String owner, long token, long now, long ttl) {
        Lease current = leases.get(jobId);
        if (current == null || !current.owner.equals(owner)) {
            return false;
        }
        leases.put(jobId, new Lease(jobId, owner, current.token, now + ttl));
        return true;
    }

    public synchronized long currentToken(String jobId) {
        Lease current = leases.get(jobId);
        return current == null ? 0L : current.token;
    }

    public synchronized Lease current(String jobId) {
        return leases.get(jobId);
    }
}
