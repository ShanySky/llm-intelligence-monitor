public final class EventConsumer {
  private final Ledger ledger;
  public EventConsumer(Ledger ledger){this.ledger=ledger;}
  private static String part(String v){return v.length()+":"+v;}
  public boolean accept(Delivery d) {
    String key=part(d.tenant)+part(d.topic)+part(d.id)+":"+d.revision;
    return ledger.apply(key,d.payload);
  }
}
