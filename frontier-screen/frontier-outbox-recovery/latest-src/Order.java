public final class Order {
    final String id;
    final String orderKey;
    String status;
    long version;

    Order(String id, String orderKey) {
        this.id = id;
        this.orderKey = orderKey;
        this.status = "PENDING";
        this.version = 0;
    }

    Order copy() {
        Order c = new Order(id, orderKey);
        c.status = status;
        c.version = version;
        return c;
    }
}
