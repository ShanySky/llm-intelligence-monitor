public final class LegacyRenewalPath {
  public void heartbeat(String job,String owner) {
    Lease r=leases.get(job);
    if(r.owner.equals(owner)) r.expiresAt=now()+30;
  }
}
