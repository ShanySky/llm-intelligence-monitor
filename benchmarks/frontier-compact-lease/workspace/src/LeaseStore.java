import java.util.*;
public final class LeaseStore {
  private static final class State {
    String owner;long expiry,epoch;boolean done;
  }
  private final Map<String,State> jobs=new HashMap<>();
  public synchronized Token acquire(String job,String owner,long now,long ttl){
    State s=jobs.computeIfAbsent(job,k->new State());
    if(s.done || (s.owner!=null && now<s.expiry))return null;
    s.owner=owner;s.expiry=now+ttl;s.epoch++;
    return new Token(job,owner,s.epoch);
  }
  public synchronized boolean renew(Token token,long now,long ttl){
    State s=jobs.get(token.job);
    if(s==null||s.done||!token.owner.equals(s.owner))return false;
    s.expiry=now+ttl;
    return true;
  }
  public synchronized boolean complete(Token token,long now){
    State s=jobs.get(token.job);
    if(s==null||s.done||!token.owner.equals(s.owner))return false;
    s.done=true;return true;
  }
  public synchronized boolean isDone(String job){return jobs.containsKey(job)&&jobs.get(job).done;}
}
