public interface ReportGenerator {
    int chunkCount();
    String chunk(int index);
}
