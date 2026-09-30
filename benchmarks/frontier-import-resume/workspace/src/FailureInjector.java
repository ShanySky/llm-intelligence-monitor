public interface FailureInjector {
    void afterUpsert(long rowId);

    static FailureInjector none() {
        return rowId -> {};
    }
}
