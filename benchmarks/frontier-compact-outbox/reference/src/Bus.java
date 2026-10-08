import java.util.*;
public final class Bus {
  private final List<String> effects=new ArrayList<>();
  private final Set<String> published=new HashSet<>();
  private boolean sendFailure;
  public synchronized void failNextSend(){sendFailure=true;}
  public synchronized void send(String id){
    if(sendFailure){sendFailure=false;throw new IllegalStateException("bus offline");}
    if(published.add(id)) effects.add(id);
  }
  public synchronized int count(){return effects.size();}
  public synchronized List<String> effects(){return new ArrayList<>(effects);}
}
