public final class EventProducer {
  public Event paid(Order order) {
    return new Event(
      UUID.randomUUID().toString(),
      order.id,
      order.version,
      null,
      order.customerKey
    );
  }
}
