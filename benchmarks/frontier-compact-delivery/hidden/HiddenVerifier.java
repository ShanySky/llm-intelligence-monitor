import java.util.*;import java.util.concurrent.*;
public final class HiddenVerifier {
 static void ok(boolean b){if(!b)throw new AssertionError();}
 static void test(String n,Runnable f){
   try{f.run();System.out.println(n+"_PASS");}
   catch(Throwable e){System.out.println(n+"_FAIL:"+e);}
 }
 static Delivery d(String tenant,String order,long ver,String line,String env,String part,long offset){
   return new Delivery(tenant,order,ver,line,env,part,offset,"fx:"+tenant+":"+order+":"+ver+":"+line);
 }
 static void preSendFailure(){
   Effects e=new Effects();Offsets s=new Offsets();Dispatcher x=new Dispatcher(s,e);
   Delivery d=d("t","o",1,"l","a","p",1);
   e.failBeforeOnce();try{x.handle(d);}catch(IllegalStateException ignored){}
   ok(s.current("p")==-1 && e.count()==0);
   ok(x.handle(d) && e.count()==1 && s.current("p")==1);
 }
 static void replyLoss(){
   Effects e=new Effects();Offsets s=new Offsets();Dispatcher x=new Dispatcher(s,e);
   Delivery first=d("t","o",3,"l","env-1","p",2);
   e.failAfterOnce();try{x.handle(first);}catch(IllegalStateException ignored){}
   ok(s.current("p")==-1 && e.count()==1);
   Delivery redelivery=d("t","o",3,"l","env-2","p",2);
   x.handle(redelivery);ok(e.count()==1 && s.current("p")==2);
 }
 static void businessIdentity(){
   Effects e=new Effects();Offsets s=new Offsets();Dispatcher x=new Dispatcher(s,e);
   x.handle(d("ab","c",1,"l","same","p",1));
   x.handle(d("a","bc",1,"l","same","p",2));
   x.handle(d("ab","c",2,"l","same","p",3));
   x.handle(d("ab","c",2,"m","same","p",4));
   x.handle(d("ab","c",2,"m","different","p",5));
   ok(e.count()==4 && s.current("p")==5);
 }
 static void concurrencyAndOffset(){
   for(int i=0;i<5;i++){
     Effects e=new Effects();Offsets s=new Offsets();
     CountDownLatch start=new CountDownLatch(1);Thread[] ts=new Thread[20];
     for(int n=0;n<ts.length;n++){
       final int k=n;
       ts[n]=new Thread(()->{
         try{start.await();}catch(InterruptedException z){throw new RuntimeException(z);}
         new Dispatcher(s,e).handle(d("t","order",9,"line","env-"+k,"p",10));
       });
       ts[n].start();
     }
     start.countDown();
     for(Thread t:ts)try{t.join(3000);}catch(InterruptedException z){throw new RuntimeException(z);}
     ok(e.count()==1 && s.current("p")==10);
     new Dispatcher(s,e).handle(d("t","new",2,"line","old","p",8));
     ok(e.count()==1 && s.current("p")==10);
     new Dispatcher(s,e).handle(d("t","other",2,"line","new","q",1));
     ok(e.count()==2 && s.current("q")==1);
   }
 }
 public static void main(String[] args){
   test("PRE_SEND",HiddenVerifier::preSendFailure);
   test("REPLY_LOSS",HiddenVerifier::replyLoss);
   test("IDENTITY",HiddenVerifier::businessIdentity);
   test("CONCURRENT_OFFSET",HiddenVerifier::concurrencyAndOffset);
 }
}
