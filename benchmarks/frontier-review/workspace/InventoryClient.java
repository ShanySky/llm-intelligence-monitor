public interface InventoryClient {
    String reserve(String orderId, String idempotencyKey);
}
