# Locking contract
Pair operations run concurrently across service instances. Every path that needs two
account locks must acquire them in canonical ascending account-id order.
