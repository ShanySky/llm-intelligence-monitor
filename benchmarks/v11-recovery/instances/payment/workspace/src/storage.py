class PaymentGateway:
    def __init__(self): self.captures = {}
    def capture(self, key, amount):
        if key not in self.captures:
            self.captures[key] = ("receipt-" + str(len(self.captures)+1), amount)
        return self.captures[key][0]
    def count(self): return len(self.captures)

class OrderStore:
    def __init__(self): self.rows = {}
    def create(self, tenant, order, version, status="pending"):
        self.rows[(tenant,order)]={"version":version,"status":status,"receipt":None}
    def get(self,tenant,order): return self.rows.get((tenant,order))
