public final class OrderService {
  private final Store store; private final Bus bus;
  public OrderService(Store store,Bus bus){this.store=store;this.bus=bus;}
  public void place(String id){
    store.create(id);
    drain();
  }
  public void drain(){
    for(String id:store.pending()){
      bus.send(id);
      store.ack(id);
    }
  }
}
