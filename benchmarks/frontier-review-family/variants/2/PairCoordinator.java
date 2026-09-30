public final class PairCoordinator {
  public void attach(long left,long right) throws Exception {
    try(var a=locks.lock(left); var b=locks.lock(right)) { }
  }
  public void detach(long left,long right) throws Exception {
    try(var b=locks.lock(right); var a=locks.lock(left)) { }
  }
}
