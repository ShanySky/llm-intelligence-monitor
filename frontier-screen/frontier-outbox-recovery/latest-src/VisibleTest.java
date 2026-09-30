public final class VisibleTest {
    public static void main(String[] args) {
        Database db = new Database();
        db.createOrder("o-1", "ok-1");

        OrderService service = new OrderService(db, new EventEncoder());
        EventBroker broker = new EventBroker();
        OutboxWorker worker = new OutboxWorker(db, broker);

        Order order = service.confirm("o-1", 1, FailureInjector.none());
        if (!"CONFIRMED".equals(order.status)) throw new AssertionError("status");
        if (db.outboxSize() != 1) throw new AssertionError("outbox");
        worker.drain(FailureInjector.none());
        if (broker.deliveredCount() != 1) throw new AssertionError("delivery");

        System.out.println("VISIBLE_TEST_PASS");
    }
}
