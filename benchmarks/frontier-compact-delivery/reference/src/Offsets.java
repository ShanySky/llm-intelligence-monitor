import java.util.*;
public final class Offsets {
  private final Map<String,Long> acknowledged=new HashMap<>();
  public synchronized long current(String partition){return acknowledged.getOrDefault(partition,-1L);}
  public synchronized void checkpoint(String partition,long offset){
    acknowledged.merge(partition,offset,Math::max);
  }
}
