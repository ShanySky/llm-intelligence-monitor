import java.util.*;
public final class HiddenVerifier {
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void run(String name,Runnable f){try{f.run();System.out.println(name+"_PASS");}catch(Throwable e){System.out.println(name+"_FAIL:"+e);}}
 static void drain(OrderService s){for(int i=0;i<3;i++)try{s.drain();}catch(IllegalStateException e){}}
 static void durable(){Store st=new Store();Bus bus=new Bus();OrderService s=new OrderService(st,bus);
  bus.failNextSend();try{s.place("d-1");}catch(IllegalStateException e){}
  check(st.exists("d-1"));check(st.pending().contains("d-1"));drain(s);
  check(bus.count()==1);check(st.pending().isEmpty());}
 static void ackWindow(){Store st=new Store();Bus bus=new Bus();OrderService s=new OrderService(st,bus);
  st.failAckOnce();try{s.place("a-1");}catch(IllegalStateException e){}
  drain(s);check(bus.count()==1);check(st.pending().isEmpty());}
 static void repeat(){Store st=new Store();Bus bus=new Bus();OrderService s=new OrderService(st,bus);
  s.place("r-1");s.place("r-1");drain(s);drain(s);check(bus.count()==1);}
 static void unrelated(){Store st=new Store();Bus bus=new Bus();OrderService s=new OrderService(st,bus);
  s.place("x-1");s.place("x-2");drain(s);check(bus.count()==2);
  check(new HashSet<>(bus.effects()).size()==2);}
 public static void main(String[] args){run("DURABLE",HiddenVerifier::durable);
  run("ACK_WINDOW",HiddenVerifier::ackWindow);run("REPEAT",HiddenVerifier::repeat);
  run("UNRELATED",HiddenVerifier::unrelated);}
}