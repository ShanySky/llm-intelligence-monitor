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
        return pageByOffset(offset, limit, ingestSeq);
    }

    /** Pages the immutable prefix identified by the job's ingest watermark. */
    public synchronized List<ImportRow> pageByOffset(int offset, int limit, long snapshot) {
        return rows.stream()
            .filter(r -> r.ingestSeq <= snapshot)
            .sorted(
                Comparator.comparingLong((ImportRow r) -> r.createdAt).reversed()
                    .thenComparing(Comparator.comparingLong((ImportRow r) -> r.id).reversed())
                    .thenComparingLong(r -> r.ingestSeq)
            )
            .skip(offset)
            .limit(limit)
            .toList();
    }
}
