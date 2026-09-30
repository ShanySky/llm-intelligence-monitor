public final class WebhookService {
  @Transactional
  public void paid(String eventId,String orderId,long version){
    if(events.exists(eventId)) return; events.insert(eventId);
    OrderState state=states.getOrCreate(orderId);
    if(version<state.version) return;
    state.version=version; state.status="PAID";
    Fulfillment f=fulfillments.findOrCreate(eventId,orderId);
    if(f.completed) return;
    String key=inventory.reserve(orderId,"event:"+eventId);
    failure.afterReserve(orderId);
    f.reservationKey=key; f.completed=true;
  }
}
