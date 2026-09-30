# Pair-operation locking contract

Pair operations execute concurrently on different service instances.

Whenever two account locks are needed, every code path must acquire them in one
canonical ascending account-id order.
