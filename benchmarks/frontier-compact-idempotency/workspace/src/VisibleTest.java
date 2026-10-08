public final class VisibleTest {
  static void check(boolean x){if(!x)throw new AssertionError();}
  public static void main(String[] args){
    Ledger ledger=new Ledger();EventConsumer consumer=new EventConsumer(ledger);
    Delivery d=new Delivery("a","paid","id-1",1,"effect");
    check(consumer.accept(d));check(!consumer.accept(d));check(ledger.count()==1);
    System.out.println("VISIBLE_PASS");
  }
}
