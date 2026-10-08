class Cache:
    def __init__(self): self.items={}
    def read(self,kind,tenant,key,loader):
        k=(kind,tenant,key)
        if k not in self.items: self.items[k]=loader()
        return self.items[k]
    def evict(self,kind,tenant,key): self.items.pop((kind,tenant,key),None)
