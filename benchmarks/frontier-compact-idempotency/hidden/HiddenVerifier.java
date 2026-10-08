import java.util.*;import java.util.concurrent.*;
public final class HiddenVerifier {
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void run(String name,Runnable fn){try{fn.run();System.out.println(name+"_PASS");}catch(Throwable e){System.out.println(name+"_FAIL:"+e);}}
 static Delivery d(String t,String topic,String id,long r){return new Delivery(t,topic,id,r,"effect");}
 static void tenant(){Ledger l=new Ledger();EventConsumer c=new EventConsumer(l);
   check(c.accept(d("t-1","paid","1",1)));check(c.accept(d("t-2","paid","1",1)));check(l.count()==2);}
 static void revision(){Ledger l=new Ledger();EventConsumer c=new EventConsumer(l);
   check(c.accept(d("t","paid","1",1)));check(c.accept(d("t","paid","1",2)));check(l.count()==2);}
 static void topic(){Ledger l=new Ledger();EventConsumer c=new EventConsumer(l);
   check(c.accept(d("t","paid","1",1)));check(c.accept(d("t","refunded","1",1)));
   check(!c.accept(d("t","paid","1",1)));check(l.count()==2);}
 static void encoding(){Ledger l=new Ledger();EventConsumer c=new EventConsumer(l);
   check(c.accept(d("ab","c","x",1)));
   check(c.accept(d("a","bc","x",1)));
   check(l.count()==2);
 }
 public static void main(String[] args){
   run("TENANT",HiddenVerifier::tenant);run("REVISION",HiddenVerifier::revision);
   run("TOPIC",HiddenVerifier::topic);run("ENCODING",HiddenVerifier::encoding);
 }
}