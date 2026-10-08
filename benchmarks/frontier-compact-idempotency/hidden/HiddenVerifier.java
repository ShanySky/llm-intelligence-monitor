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
 static void parallel(){for(int n=0;n<8;n++){Ledger l=new Ledger();EventConsumer c=new EventConsumer(l);
    CountDownLatch start=new CountDownLatch(1);Thread[] ts=new Thread[36];
    for(int i=0;i<ts.length;i++){ts[i]=new Thread(()->{try{start.await();}catch(Exception e){throw new RuntimeException(e);}c.accept(d("t","paid","id",1));});ts[i].start();}
    start.countDown();for(Thread t:ts)try{t.join(3000);}catch(InterruptedException e){throw new RuntimeException(e);}
    check(l.count()==1);}}
 public static void main(String[] args){
   run("TENANT",HiddenVerifier::tenant);run("REVISION",HiddenVerifier::revision);
   run("TOPIC",HiddenVerifier::topic);run("PARALLEL",HiddenVerifier::parallel);
 }
}