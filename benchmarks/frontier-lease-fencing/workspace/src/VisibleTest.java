public final class VisibleTest {
    public static void main(String[] args) {
        LeaseStore leases = new LeaseStore();
        ResultStore results = new ResultStore();
        CancellationStore cancellations = new CancellationStore();
        BillingAdapter billing = new BillingAdapter();
        JobRunner runner = new JobRunner(leases, results, cancellations, billing);

        Lease lease = runner.begin("job-1", "worker-a", 100, 50);
        runner.finish("job-1", lease, "DONE", FailureInjector.none());

        if (!"DONE".equals(results.get("job-1"))) throw new AssertionError("result");
        if (billing.effectCount() != 1) throw new AssertionError("effect");

        System.out.println("VISIBLE_TEST_PASS");
    }
}
