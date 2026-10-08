import java.util.*;
public final class Effects {
  private final Set<String> keys=new HashSet<>();
  private final List<String> emitted=new ArrayList<>();
  private boolean beforeFailure=false,afterFailure=false;
  public synchronized void failBeforeOnce(){beforeFailure=true;}
  public synchronized void failAfterOnce(){afterFailure=true;}
  public synchronized boolean send(String key,String value) {
    if(beforeFailure){beforeFailure=false;throw new IllegalStateException("before send");}
    if(keys.contains(key))return false;
    keys.add(key);emitted.add(value);
    if(afterFailure){afterFailure=false;throw new IllegalStateException("reply lost");}
    return true;
  }
  public synchronized int count(){return emitted.size();}
  public synchronized List<String> values(){return new ArrayList<>(emitted);}
}
