public final class OrderRecord {
    final String id;
    long sequence = 0;

    String legacyStatus = null;
    long legacyVersion = -1;

    Integer statusCode = null;
    String statusReason = null;
    long newVersion = -1;

    OrderRecord(String id) {
        this.id = id;
    }

    long nextVersion() {
        return ++sequence;
    }
}
