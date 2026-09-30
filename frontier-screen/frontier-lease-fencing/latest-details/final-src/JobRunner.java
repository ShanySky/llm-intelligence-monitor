public final class JobRunner {
    private final LeaseStore leases;
    private final ResultStore results;
    private final CancellationStore cancellations;
    private final BillingAdapter billing;

    public JobRunner(
        LeaseStore leases,
        ResultStore results,
        CancellationStore cancellations,
        BillingAdapter billing
    ) {
        this.leases = leases;
        this.results = results;
        this.cancellations = cancellations;
        this.billing = billing;
    }

    public Lease begin(String jobId, String workerId, long now, long ttl) {
        return leases.acquire(jobId, workerId, now, ttl);
    }

    public void finish(String jobId, Lease lease, String value, FailureInjector failure) {
        leases.runIfCurrent(lease, () -> {
            if (cancellations.isCancelled(jobId)) {
                results.save(jobId, lease.token, "CANCELLED");
                return;
            }

            // The lease token fences coordination, but is not part of the business identity.
            billing.apply(jobId);
            failure.afterExternalEffect(jobId, lease.token);
            if (!cancellations.isCancelled(jobId)) {
                results.save(jobId, lease.token, value);
            }
        });
    }

    public void cancel(String jobId) {
        leases.runExclusive(() -> {
            cancellations.cancel(jobId);
            results.save(jobId, leases.currentToken(jobId), "CANCELLED");
        });
    }
}
