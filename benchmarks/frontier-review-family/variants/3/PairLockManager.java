public final class PairLockManager {
  public void merge(long a,long b) throws Exception {
    try(var x=locks.lock(a); var y=locks.lock(b)) { }
  }
  public void split(long a,long b) throws Exception {
    try(var y=locks.lock(b); var x=locks.lock(a)) { }
  }
}
