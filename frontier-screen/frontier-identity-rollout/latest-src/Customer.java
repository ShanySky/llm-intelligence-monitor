public final class Customer {
    final long id;
    volatile String customerKey;
    String name;

    Customer(long id, String name) {
        this.id = id;
        this.name = name;
    }
}
