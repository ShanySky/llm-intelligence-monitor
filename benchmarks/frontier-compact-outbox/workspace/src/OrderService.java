public final class OrderService {
  private final Store store; private final Bus bus;
  public OrderService(Store store,Bus bus){this.store=store;this.bus=bus;}
  public void place(String id){
    if(store.create(id)) bus.send(id);
  }
  public void drain(){
    for(String id:store.pending()){
      bus.send(id);
      store.ack(id);
    }
  }
}
