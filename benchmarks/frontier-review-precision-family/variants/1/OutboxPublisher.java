public final class OutboxPublisher {
  public void publish(OutboxRecord r) {
    sink.send(r.eventKey(),r.payload());
    outbox.markSent(r.eventKey());
  }
}
