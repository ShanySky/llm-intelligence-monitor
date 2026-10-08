public final class Delivery {
  public final String tenant, order, line, deliveryId, partition, payload;
  public final long orderVersion, offset;
  public Delivery(String tenant,String order,long orderVersion,String line,
                  String deliveryId,String partition,long offset,String payload) {
    this.tenant=tenant;this.order=order;this.orderVersion=orderVersion;
    this.line=line;this.deliveryId=deliveryId;this.partition=partition;
    this.offset=offset;this.payload=payload;
  }
}
