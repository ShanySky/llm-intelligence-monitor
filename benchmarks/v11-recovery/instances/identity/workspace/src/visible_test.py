from storage import CustomerStore
from cache import Cache
from service import IdentityService
s,c=CustomerStore(),Cache()
s.create("a",1,"key","new")
x=IdentityService(s,c)
assert x.legacy_read("a",1)=="new"
x.legacy_write("a",1,"paid")
assert x.legacy_read("a",1)=="paid"
print("VISIBLE_PASS")
