class Worker:
    def __init__(self, leases, effects): self.leases,self.effects=leases,effects
    def commit(self, job, owner, token, now, operation, between_check=None):
        if not self.leases.valid(job,owner,token,now): return False
        if between_check: between_check()
        return self.leases.perform_if_owned(job,owner,token,now,lambda:self.effects.apply(job,operation))
