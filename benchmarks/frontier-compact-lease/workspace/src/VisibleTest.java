public final class VisibleTest {
  static void check(boolean x){if(!x)throw new AssertionError();}
  public static void main(String[] args){
    LeaseStore store=new LeaseStore();
    Token lease=store.acquire("j-1","worker",0,20);
    check(lease!=null);check(store.complete(lease,1));check(store.isDone("j-1"));
    System.out.println("VISIBLE_PASS");
  }
}
