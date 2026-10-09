class SettlementService:
    def __init__(self, orders, gateway): self.orders, self.gateway = orders, gateway
    def pay(self, tenant, order, version, delivery_id, amount, after_capture=None):
        row=self.orders.get(tenant,order)
        if row is None: return False
        row["status"]="paid"
        receipt=self.gateway.capture(delivery_id,amount)
        if after_capture: after_capture()
        row["receipt"]=receipt
        return True
