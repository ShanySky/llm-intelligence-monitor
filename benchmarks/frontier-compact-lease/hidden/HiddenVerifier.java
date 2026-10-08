public final class HiddenVerifier {
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void run(String name,Runnable f){try{f.run();System.out.println(name+"_PASS");}catch(Throwable e){System.out.println(name+"_FAIL:"+e);}}
 static void stale(){LeaseStore s=new LeaseStore();
  Token old=s.acquire("j","same",0,10);Token now=s.acquire("j","same",10,10);
  check(now!=null && now.epoch>old.epoch);check(!s.complete(old,11));
  check(s.complete(now,11));check(s.isDone("j"));}
 static void deadline(){LeaseStore s=new LeaseStore();
  Token t=s.acquire("j","a",0,10);check(!s.complete(t,10));
  check(s.acquire("j","b",10,10)!=null);check(!s.renew(t,10,50));}
 static void renew(){LeaseStore s=new LeaseStore();
  Token old=s.acquire("j","a",0,5);Token later=s.acquire("j","a",5,10);
  check(!s.renew(old,6,60));check(s.renew(later,6,10));
  check(s.acquire("j","other",7,10)==null);}
 static void separate(){LeaseStore s=new LeaseStore();
  Token a=s.acquire("a","owner",0,10);Token b=s.acquire("b","owner",0,10);
  check(a!=null&&b!=null);check(s.complete(a,2));check(!s.complete(a,3));
  check(!s.isDone("b"));check(s.complete(b,2));check(s.acquire("a","x",11,5)==null);}
 public static void main(String[] args){run("STALE",HiddenVerifier::stale);
  run("DEADLINE",HiddenVerifier::deadline);run("RENEW",HiddenVerifier::renew);
  run("SEPARATE",HiddenVerifier::separate);}
}