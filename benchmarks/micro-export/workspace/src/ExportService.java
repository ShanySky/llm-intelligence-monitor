public final class ExportService {
    private final JobRepository jobs;
    private final ArtifactStore artifacts;
    private final FailureInjector failureInjector;

    public ExportService(JobRepository jobs, ArtifactStore artifacts, FailureInjector failureInjector) {
        this.jobs = jobs;
        this.artifacts = artifacts;
        this.failureInjector = failureInjector;
    }

    public void requestCancel(String jobId) {
        jobs.get(jobId).cancelRequested = true;
    }

    public void run(String jobId, ReportGenerator generator) {
        ExportJob job = jobs.get(jobId);
        if (job.state != ExportJob.State.PENDING) {
            return;
        }

        job.state = ExportJob.State.RUNNING;

        StringBuilder output = new StringBuilder();
        for (int i = 0; i < generator.chunkCount(); i++) {
            output.append(generator.chunk(i));
        }

        String key = artifacts.uploadNew(jobId, output.toString());
        failureInjector.afterPublish(jobId);

        job.artifactKey = key;
        job.state = ExportJob.State.COMPLETED;
    }
}
