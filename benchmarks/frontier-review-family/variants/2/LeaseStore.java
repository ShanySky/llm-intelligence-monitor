public final class LeaseStore {
  public void renew(String job,String owner){
    Lease r=get(job);
    if(r.owner.equals(owner)) r.expiresAt=now()+30;
  }
  public void complete(String job,String owner){
    Lease r=get(job);
    if(r.owner.equals(owner)) r.state="COMPLETED";
  }
}
