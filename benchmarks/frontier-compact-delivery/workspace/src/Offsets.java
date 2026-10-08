import java.util.*;
public final class Offsets {
  private final Map<String,Long> acknowledged=new HashMap<>();
  public long current(String partition){return acknowledged.getOrDefault(partition,-1L);}
  public void checkpoint(String partition,long offset){acknowledged.put(partition,offset);}
}
