public final class Metrics {
    private int reads;
    public void recordRead() { reads++; }
    public int reads() { return reads; }
}
