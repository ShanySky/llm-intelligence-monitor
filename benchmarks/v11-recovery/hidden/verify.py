#!/usr/bin/env python3
"""Hidden checks run from host. Never include this module in an agent workspace."""
import sys
from pathlib import Path
variant,root=sys.argv[1],Path(sys.argv[2]).resolve()
sys.path.insert(0,str(root/"src"))
def run(name,fn):
    try: fn(); print(name+"_PASS")
    except Exception as ex: print(name+"_FAIL:"+repr(ex))
if variant=="payment":
    from storage import PaymentGateway,OrderStore
    from service import SettlementService
    def setup(tenant="a",order="o",version=1,status="pending"):
        o,g=OrderStore(),PaymentGateway();o.create(tenant,order,version,status)
        return o,g,SettlementService(o,g)
    def replay():
        o,g,s=setup()
        assert s.pay("a","o",1,"first",5)
        assert s.pay("a","o",1,"second",5)
        assert g.count()==1
    def crash():
        o,g,s=setup()
        def fail(): raise RuntimeError("lost ack")
        try: s.pay("a","o",1,"first",5,fail)
        except RuntimeError: pass
        assert s.pay("a","o",1,"second",5)
        assert g.count()==1 and o.get("a","o")["receipt"]
    def scope():
        o,g,s=setup()
        o.create("b","o",1);o.create("a","o2",1)
        assert s.pay("a","o",1,"d",5) and s.pay("b","o",1,"d",6)
        o.create("a","o",2)
        assert s.pay("a","o",2,"d",7) and g.count()==3
    def guard():
        o,g,s=setup(status="cancelled")
        assert not s.pay("a","o",1,"d",5)
        o.create("b","b",2)
        assert not s.pay("b","b",1,"d2",5)
        assert not s.pay("none","none",1,"d3",5) and g.count()==0
    cases=[("REPLAY",replay),("CRASH",crash),("SCOPE",scope),("GUARD",guard)]
elif variant=="lease":
    from storage import LeaseStore
    from effects import EffectLog
    from worker import Worker
    def setup():
        l,e=LeaseStore(),EffectLog()
        return l,e,Worker(l,e)
    def race():
        l,e,w=setup();t=l.acquire("job","old",0,5)
        def handoff(): assert l.acquire("job","new",6,5)!=t
        assert not w.commit("job","old",t,1,"ship",handoff) and e.count()==0
    def expire():
        l,e,w=setup();t=l.acquire("job","owner",0,5)
        assert not w.commit("job","owner",t,6,"ship") and e.count()==0
    def retry():
        l,e,w=setup();t=l.acquire("job","owner",0,5)
        assert l.renew("job","owner",t,4,8)
        assert w.commit("job","owner",t,9,"ship")
        assert not w.commit("job","owner",t,10,"ship") and e.count()==1
    def isolate():
        l,e,w=setup();a=l.acquire("a","w",0,3);b=l.acquire("b","w",0,8)
        assert not w.commit("a","w",a,5,"send")
        assert w.commit("b","w",b,5,"send") and e.count()==1
    cases=[("RACE",race),("EXPIRE",expire),("RETRY",retry),("ISOLATE",isolate)]
elif variant=="identity":
    from storage import CustomerStore
    from cache import Cache
    from service import IdentityService
    def setup():
        s,c=CustomerStore(),Cache();s.create("a",1,"key","open")
        return s,c,IdentityService(s,c)
    def legacy():
        s,c,x=setup()
        assert x.v2_read("a","key")=="open"
        x.legacy_write("a",1,"paid")
        assert x.v2_read("a","key")=="paid"
    def v2():
        s,c,x=setup()
        assert x.legacy_read("a",1)=="open"
        x.v2_write("a","key","paid")
        assert x.legacy_read("a",1)=="paid"
    def stale():
        s,c,x=setup();rev=s.by_legacy("a",1)["revision"]
        x.legacy_write("a",1,"paid")
        assert not x.apply_backfill("a",1,rev,"open")
        assert s.by_legacy("a",1)["new_status"] is None
    def tenant():
        s,c,x=setup();s.create("b",1,"key","different")
        rev=s.by_legacy("a",1)["revision"]
        assert x.apply_backfill("a",1,rev,"open")
        assert s.by_legacy("b",1)["new_status"] is None
        assert x.v2_read("a","key")=="open" and x.v2_read("b","key")=="different"
    cases=[("LEGACY",legacy),("V2",v2),("STALE",stale),("TENANT",tenant)]
else: raise SystemExit("unknown variant")
for name,fn in cases: run(name,fn)
