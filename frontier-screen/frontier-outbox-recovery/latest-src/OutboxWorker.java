public final class OutboxWorker {
    private final Database db;
    private final EventBroker broker;

    public OutboxWorker(Database db, EventBroker broker) {
        this.db = db;
        this.broker = broker;
    }

    public void drain(FailureInjector failure) {
        for (OutboxRecord record : db.pendingOutbox()) {
            broker.publish(record.eventId, record.payload);
            failure.afterPublish(record.eventId);
            db.markSent(record.eventId);
        }
    }
}
