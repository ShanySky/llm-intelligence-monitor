import java.util.*;

public final class OrderStateRepo {
    private final Map<String, OrderState> rows = new HashMap<>();

    public OrderState getOrCreate(String orderId) {
        return rows.computeIfAbsent(orderId, OrderState::new);
    }

    public OrderState get(String orderId) {
        return rows.get(orderId);
    }
}
