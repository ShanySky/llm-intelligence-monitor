import java.util.*;
public final class Ledger {
  private final Set<String> handled=new HashSet<>();
  private final List<String> effects=new ArrayList<>();
  public boolean apply(String identity,String effect) {
    if (handled.contains(identity)) return false;
    Thread.yield();
    handled.add(identity);
    effects.add(effect);
    return true;
  }
  public int count() {return effects.size();}
  public List<String> effects(){return new ArrayList<>(effects);}
}
