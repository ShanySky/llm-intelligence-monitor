public final class Customer {
    final long id;
    String stableKey;
    String legacyStatus;
    String newStatus;
    long version;

    Customer(long id,String stableKey,String status,long version) {
        this.id=id; this.stableKey=stableKey; this.legacyStatus=status;
        this.newStatus=status; this.version=version;
    }
}
