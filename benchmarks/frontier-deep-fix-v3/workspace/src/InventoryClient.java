public interface InventoryClient {
    /**
     * Reservation is an external side effect. Reusing one idempotency key is
     * safe and returns the same logical reservation; a different key may create
     * another reservation for the same order.
     */
    String reserve(String orderId, String idempotencyKey);
}
