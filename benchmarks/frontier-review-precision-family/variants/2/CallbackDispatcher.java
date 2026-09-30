public final class CallbackDispatcher {
  public void send(Job job,String deliveryId) {
    remote.post(job.callbackUrl(),"delivery:"+deliveryId,job.payload());
  }
}
