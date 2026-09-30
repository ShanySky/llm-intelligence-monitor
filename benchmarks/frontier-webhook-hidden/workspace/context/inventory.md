# Inventory side-effect contract

- reserve(orderId, idempotencyKey) is an external call.
- Reusing the same idempotencyKey is safe and returns the same logical reservation.
- Different idempotency keys may create different reservations for the same order.
- The process can crash after reserve succeeds but before local state records the
  returned reservation key.
- release(reservationKey) removes that logical reservation.
