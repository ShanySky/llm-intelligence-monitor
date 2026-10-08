# Task: reliable fulfillment dispatch

An order may be accepted during a transport outage. After recovery its fulfillment event can be missing, or a retry can dispatch twice. Repair the small service using contracts found throughout this workspace.

Preserve Store, Bus and OrderService public method signatures. Do not remove retries or silently drop accepted orders. Run visible tests; hidden tests cover crash windows and retry behavior. Do not modify tests/contracts.
