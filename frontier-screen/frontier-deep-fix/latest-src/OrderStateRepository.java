public interface OrderStateRepository {
    OrderState getOrCreate(String orderId);
}
