public final class Lease {
    final String jobId;
    final String owner;
    final long token;
    final long expiresAt;

    Lease(String jobId, String owner, long token, long expiresAt) {
        this.jobId = jobId;
        this.owner = owner;
        this.token = token;
        this.expiresAt = expiresAt;
    }
}
