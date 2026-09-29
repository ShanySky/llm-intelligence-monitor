public final class ExportJob {
    public enum State {
        PENDING,
        RUNNING,
        CANCELLED,
        COMPLETED
    }

    private final String id;
    State state = State.PENDING;
    boolean cancelRequested = false;
    String artifactKey = null;

    public ExportJob(String id) {
        this.id = id;
    }

    public String id() {
        return id;
    }

    public State state() {
        return state;
    }

    public boolean cancelRequested() {
        return cancelRequested;
    }

    public String artifactKey() {
        return artifactKey;
    }
}
