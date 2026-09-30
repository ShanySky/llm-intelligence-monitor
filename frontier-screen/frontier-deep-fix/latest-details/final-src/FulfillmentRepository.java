public interface FulfillmentRepository {
    Fulfillment findOrCreate(String key, String orderId);
}
