public final class ReservationMover {
  public void move(long from,long to) throws Exception {
    try(var a=locks.lock(from); var b=locks.lock(to)) { }
  }
  public void cancelPair(long first,long second) throws Exception {
    try(var b=locks.lock(second); var a=locks.lock(first)) { }
  }
}
