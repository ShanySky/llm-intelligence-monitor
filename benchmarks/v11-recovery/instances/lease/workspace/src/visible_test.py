from storage import LeaseStore
from effects import EffectLog
from worker import Worker
l,e=LeaseStore(),EffectLog()
t=l.acquire("job","a",0,10)
assert Worker(l,e).commit("job","a",t,1,"ship") and e.count()==1
print("VISIBLE_PASS")
