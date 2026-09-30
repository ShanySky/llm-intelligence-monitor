import java.util.*;

public final class ImportSource {
    private final List<ImportRow> rows = new ArrayList<>();
    private long ingestSeq = 0;

    public synchronized ImportRow add(long id, long createdAt, String value) {
        ImportRow row = new ImportRow(id, createdAt, ++ingestSeq, value);
        rows.add(row);
        return row;
    }

    public synchronized long snapshot() {
        return ingestSeq;
    }

    public synchronized List<ImportRow> pageByOffset(int offset, int limit) {
        return orderedRows().stream().skip(offset).limit(limit).toList();
    }

    synchronized List<ImportRow> pageAfter(long snapshot, long beforeCreatedAt,
                                            long beforeId, long beforeIngestSeq, int limit) {
        Comparator<ImportRow> order = order();
        return rows.stream()
            .filter(r -> r.ingestSeq <= snapshot)
            .filter(r -> order.compare(r, new ImportRow(beforeId, beforeCreatedAt, beforeIngestSeq, "")) > 0)
            .sorted(order)
            .limit(limit)
            .toList();
    }

    private List<ImportRow> orderedRows() {
        return rows.stream().sorted(order()).toList();
    }

    private static Comparator<ImportRow> order() {
        return Comparator.comparingLong((ImportRow r) -> r.createdAt).reversed()
            .thenComparing(Comparator.comparingLong((ImportRow r) -> r.id).reversed())
            .thenComparing(Comparator.comparingLong((ImportRow r) -> r.ingestSeq).reversed());
    }
}
