class CustomerStore:
    def __init__(self): self.rows={}
    def create(self,tenant,legacy,stable,status,revision=1):
        self.rows[(tenant,legacy)]={"tenant":tenant,"legacy":legacy,"stable":stable,"status":status,"new_status":None,"revision":revision}
    def by_legacy(self,tenant,legacy): return self.rows[(tenant,legacy)]
    def by_stable(self,tenant,stable):
        for row in self.rows.values():
            if row["tenant"]==tenant and row["stable"]==stable: return row
        raise KeyError((tenant,stable))
