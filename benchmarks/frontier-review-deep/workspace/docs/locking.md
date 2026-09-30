# Pair-operation locking

Pair operations can execute concurrently on different service instances.
Whenever two account locks are needed, every code path must acquire them in the
same canonical ascending account-id order.
