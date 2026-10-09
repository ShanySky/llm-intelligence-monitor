class EffectLog:
    def __init__(self): self.operations=set()
    def apply(self,job,operation):
        key=(job,operation)
        if key in self.operations: return False
        self.operations.add(key)
        return True
    def count(self): return len(self.operations)
