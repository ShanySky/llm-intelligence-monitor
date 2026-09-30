public final class ReplayCompactor {
  public void compact(List<Event> stored) {
    for (Event e : stored) {
      e.customerId = null;
    }
  }
}
