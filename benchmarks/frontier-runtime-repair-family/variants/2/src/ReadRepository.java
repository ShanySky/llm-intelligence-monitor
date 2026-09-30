public final class ReadRepository {
    private String primary;
    private String replica;
    public ReadRepository(String value) { primary=value; replica=value; }
    public void write(String value) { primary=value; }
    public void replicate() { replica=primary; }
    public String primary() { return primary; }
    public String replica() { return replica; }
}
