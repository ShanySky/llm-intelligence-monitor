public final class Dispatcher {
  private final Offsets offsets;private final Effects effects;
  public Dispatcher(Offsets offsets,Effects effects){this.offsets=offsets;this.effects=effects;}
  private static String part(String s){return s.length()+":"+s;}
  public boolean handle(Delivery d){
    if(d.offset<=offsets.current(d.partition))return false;
    String key=part(d.tenant)+part(d.order)+part(Long.toString(d.orderVersion))+part(d.line);
    boolean changed=effects.send(key,d.payload);
    offsets.checkpoint(d.partition,d.offset);
    return changed;
  }
}
