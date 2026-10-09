from storage import PaymentGateway,OrderStore
from service import SettlementService
o,g=OrderStore(),PaymentGateway()
o.create("t","o",1)
assert SettlementService(o,g).pay("t","o",1,"d",20)
assert o.get("t","o")["status"]=="paid" and g.count()==1
print("VISIBLE_PASS")
