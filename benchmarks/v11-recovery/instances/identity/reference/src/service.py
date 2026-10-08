class IdentityService:
    def __init__(self,store,cache): self.store,self.cache=store,cache
    def _evict(self,row):
        self.cache.evict("legacy",row["tenant"],row["legacy"])
        self.cache.evict("stable",row["tenant"],row["stable"])
    def legacy_read(self,tenant,legacy):
        return self.cache.read("legacy",tenant,legacy,lambda:self.store.by_legacy(tenant,legacy)["status"])
    def v2_read(self,tenant,stable):
        return self.cache.read("stable",tenant,stable,lambda:self.store.by_stable(tenant,stable)["status"])
    def legacy_write(self,tenant,legacy,status):
        row=self.store.by_legacy(tenant,legacy)
        row["status"],row["revision"]=status,row["revision"]+1
        self._evict(row)
    def v2_write(self,tenant,stable,status):
        row=self.store.by_stable(tenant,stable)
        row["status"],row["revision"]=status,row["revision"]+1
        self._evict(row)
    def apply_backfill(self,tenant,legacy,observed_revision,status):
        row=self.store.by_legacy(tenant,legacy)
        if row["revision"]!=observed_revision: return False
        row["new_status"]=status
        return True
