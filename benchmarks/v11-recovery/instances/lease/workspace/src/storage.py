from threading import RLock
class LeaseStore:
    def __init__(self):
        self.lock=RLock(); self.leases={}; self.generations={}
    def acquire(self,job,owner,now,ttl):
        with self.lock:
            row=self.leases.get(job)
            if row and now<row["expiry"]: return None
            token=self.generations.get(job,0)+1
            self.generations[job]=token
            self.leases[job]={"owner":owner,"token":token,"expiry":now+ttl}
            return token
    def valid(self,job,owner,token,now):
        with self.lock:
            row=self.leases.get(job)
            return bool(row and row["owner"]==owner and row["token"]==token and now<row["expiry"])
    def renew(self,job,owner,token,now,ttl):
        with self.lock:
            if not self.valid(job,owner,token,now): return False
            self.leases[job]["expiry"]=now+ttl
            return True
    def perform_if_owned(self,job,owner,token,now,fn):
        with self.lock:
            if not self.valid(job,owner,token,now): return False
            return fn()
