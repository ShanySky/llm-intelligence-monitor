public final class VisibleTest {
    public static void main(String[] args) {
        ImportSource source = new ImportSource();
        source.add(3L, 300L, "c");
        source.add(2L, 200L, "b");
        source.add(1L, 100L, "a");

        CheckpointStore checkpoints = new CheckpointStore();
        CustomerApi api = new CustomerApi();
        ImportWorker worker = new ImportWorker(source, checkpoints, api);

        worker.run("job-visible", FailureInjector.none());

        check(api.effectCount() == 3);
        check(api.hasRow(1L) && api.hasRow(2L) && api.hasRow(3L));
        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
