public final class LeaseWorker {
  public void run(String job,String owner){
    Lease lease=leases.acquire(job,owner);
    publisher.publish(job,UUID.randomUUID().toString());
    failure.afterPublish(job);
    leases.complete(job,owner);
  }
}
