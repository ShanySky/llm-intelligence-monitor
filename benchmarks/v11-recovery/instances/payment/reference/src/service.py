class SettlementService:
    def __init__(self, orders, gateway): self.orders, self.gateway = orders, gateway
    def pay(self, tenant, order, version, delivery_id, amount, after_capture=None):
        row=self.orders.get(tenant,order)
        if row is None or row["version"]!=version or row["status"]=="cancelled": return False
        receipt=self.gateway.capture((tenant,order,version),amount)
        if after_capture: after_capture()
        row=self.orders.get(tenant,order)
        if row is None or row["version"]!=version or row["status"]=="cancelled": return False
        row["status"],row["receipt"]="paid",receipt
        return True
