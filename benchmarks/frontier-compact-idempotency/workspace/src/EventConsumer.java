public final class EventConsumer {
  private final Ledger ledger;
  public EventConsumer(Ledger ledger) {this.ledger=ledger;}
  public boolean accept(Delivery delivery) {
    return ledger.apply(delivery.id,delivery.payload);
  }
}
