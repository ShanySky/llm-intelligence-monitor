import java.util.*;
public final class Effects {
  private final Set<String> keys=new HashSet<>();
  private final List<String> emitted=new ArrayList<>();
  private boolean beforeFailure=false,afterFailure=false;
  public void failBeforeOnce(){beforeFailure=true;}
  public void failAfterOnce(){afterFailure=true;}
  public boolean send(String key,String value) {
    if(beforeFailure){beforeFailure=false;throw new IllegalStateException("before send");}
    if(keys.contains(key))return false;
    Thread.yield();
    keys.add(key);emitted.add(value);
    if(afterFailure){afterFailure=false;throw new IllegalStateException("reply lost");}
    return true;
  }
  public int count(){return emitted.size();}
  public List<String> values(){return new ArrayList<>(emitted);}
}
