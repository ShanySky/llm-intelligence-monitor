public final class BackfillJob {
  public void apply(Item captured){
    Customer c=store.get(captured.id());
    c.newStatus=captured.legacyStatus();
    c.newVersion=captured.legacyVersion();
  }
}
