import java.util.*;
public final class Ledger {
  private final Set<String> handled=new HashSet<>();
  private final List<String> effects=new ArrayList<>();
  public synchronized boolean apply(String identity,String effect) {
    if (handled.contains(identity)) return false;
    handled.add(identity);
    effects.add(effect);
    return true;
  }
  public synchronized int count(){return effects.size();}
  public synchronized List<String> effects(){return new ArrayList<>(effects);}
}
