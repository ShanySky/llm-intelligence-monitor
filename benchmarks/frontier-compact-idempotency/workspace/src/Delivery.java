public final class Delivery {
  public final String tenant, topic, id, payload;
  public final long revision;
  public Delivery(String tenant, String topic, String id, long revision, String payload) {
    this.tenant=tenant; this.topic=topic; this.id=id;
    this.revision=revision; this.payload=payload;
  }
}
