public final class FulfillmentConsumer {
  private final Set<String> processed = new HashSet<>();

  public void on(Event event) {
    if (!processed.add(event.eventId)) return;
    inventory.reserve(event.orderId, "delivery:" + event.eventId);
  }
}
