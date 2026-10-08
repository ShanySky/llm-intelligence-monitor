public final class VisibleTest {
  static void check(boolean x){if(!x)throw new AssertionError();}
  public static void main(String[] args){
    Store store=new Store();Bus bus=new Bus();OrderService service=new OrderService(store,bus);
    service.place("o-1");service.drain();check(store.exists("o-1"));check(bus.count()==1);
    System.out.println("VISIBLE_PASS");
  }
}
