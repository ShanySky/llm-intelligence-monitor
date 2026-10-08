public final class VisibleTest {
  static void ok(boolean condition){if(!condition)throw new AssertionError();}
  public static void main(String[] args){
    Offsets offsets=new Offsets();Effects effects=new Effects();
    Dispatcher dispatcher=new Dispatcher(offsets,effects);
    Delivery d=new Delivery("t","o",1,"line","envelope","partition-1",1,"value");
    ok(dispatcher.handle(d));
    ok(!dispatcher.handle(d));
    ok(effects.count()==1 && offsets.current("partition-1")==1);
    System.out.println("VISIBLE_PASS");
  }
}
