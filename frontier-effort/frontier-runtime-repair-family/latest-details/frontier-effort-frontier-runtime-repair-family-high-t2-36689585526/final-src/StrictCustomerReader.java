public final class StrictCustomerReader {
    private final ReadRepository repo;
    public StrictCustomerReader(ReadRepository repo) { this.repo = repo; }

    public String strictRead() {
        return repo.primary();
    }

    public String ordinaryRead() {
        return repo.replica();
    }
}
