public interface FulfillmentRepository {
    /**
     * The caller chooses the logical grouping key. Calls with the same key
     * observe the same fulfillment state.
     */
    Fulfillment findOrCreate(String key, String orderId);
}
