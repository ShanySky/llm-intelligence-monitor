public final class PairCoordinator {
  public void attach(long a,long b) throws Exception {
    long first=Math.min(a,b), second=Math.max(a,b);
    try(var x=locks.lock(first); var y=locks.lock(second)) { }
  }
  public void detach(long a,long b) throws Exception {
    try(var x=locks.lock(b); var y=locks.lock(a)) { }
  }
}
