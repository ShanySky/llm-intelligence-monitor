public final class Dispatcher {
  private final Offsets offsets;private final Effects effects;
  public Dispatcher(Offsets offsets,Effects effects){this.offsets=offsets;this.effects=effects;}
  public boolean handle(Delivery delivery){
    if(delivery.offset<=offsets.current(delivery.partition))return false;
    offsets.checkpoint(delivery.partition,delivery.offset);
    return effects.send(delivery.deliveryId,delivery.payload);
  }
}
