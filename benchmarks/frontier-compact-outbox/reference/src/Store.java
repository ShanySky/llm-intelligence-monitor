import java.util.*;
public final class Store {
  private final Set<String> orders=new HashSet<>();
  private final LinkedHashSet<String> pending=new LinkedHashSet<>();
  private boolean ackFailure;
  public synchronized boolean create(String id){
    if(!orders.add(id))return false;
    pending.add(id);
    return true;
  }
  public synchronized boolean exists(String id){return orders.contains(id);}
  public synchronized void stage(String id){
    if(!orders.contains(id))throw new IllegalArgumentException("unknown order");
    pending.add(id);
  }
  public synchronized List<String> pending(){return new ArrayList<>(pending);}
  public synchronized void failAckOnce(){ackFailure=true;}
  public synchronized void ack(String id){
    if(ackFailure){ackFailure=false;throw new IllegalStateException("ack lost");}
    pending.remove(id);
  }
}
