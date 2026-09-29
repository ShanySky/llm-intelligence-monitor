public final class VisibleTest {
    public static void main(String[] args) {
        JobRepository jobs = new JobRepository();
        ArtifactStore artifacts = new ArtifactStore();
        ExportService service = new ExportService(jobs, artifacts, FailureInjector.none());

        jobs.create("happy");
        service.run("happy", new ReportGenerator() {
            public int chunkCount() { return 3; }
            public String chunk(int index) {
                return new String[] {"A", "B", "C"}[index];
            }
        });

        ExportJob job = jobs.get("happy");
        check(job.state() == ExportJob.State.COMPLETED, "happy job must complete");
        check(job.artifactKey() != null, "artifact key must be recorded");
        check(artifacts.countForJob("happy") == 1, "happy path must publish exactly one artifact");
        check("ABC".equals(artifacts.get(job.artifactKey())), "artifact contents must match");

        System.out.println("VISIBLE_TEST_PASS");
    }

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
