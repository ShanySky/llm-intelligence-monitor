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
        return orderedRows().skip(offset).limit(limit).toList();
    }

    synchronized List<ImportRow> page(long snapshot, Checkpoint checkpoint, int limit) {
        Comparator<ImportRow> ordering = ordering();
        return rows.stream()
            .filter(r -> r.ingestSeq <= snapshot)
            .filter(r -> !checkpoint.hasCursor || ordering.compare(r, cursorRow(checkpoint)) > 0)
            .sorted(ordering)
            .limit(limit)
            .toList();
    }

    private ImportRow cursorRow(Checkpoint c) {
        return new ImportRow(c.beforeId, c.beforeCreatedAt, c.beforeIngestSeq, "");
    }

    private java.util.stream.Stream<ImportRow> orderedRows() {
        return rows.stream().sorted(ordering());
    }

    private Comparator<ImportRow> ordering() {
        return Comparator.comparingLong((ImportRow r) -> r.createdAt).reversed()
            .thenComparing(Comparator.comparingLong((ImportRow r) -> r.id).reversed())
            .thenComparing(Comparator.comparingLong((ImportRow r) -> r.ingestSeq).reversed());
    }
}
