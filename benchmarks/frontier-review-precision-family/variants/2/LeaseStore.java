public final class LeaseStore {
  public boolean renew(String job,String owner,long epoch) {
    Lease r=get(job);
    if(!r.owner.equals(owner) || r.epoch!=epoch) return false;
    r.expiresAt=now()+30;
    return true;
  }
  public boolean complete(String job,String owner,long epoch) {
    Lease r=get(job);
    if(!r.owner.equals(owner) || r.epoch!=epoch) return false;
    r.state="COMPLETED";
    return true;
  }
}
