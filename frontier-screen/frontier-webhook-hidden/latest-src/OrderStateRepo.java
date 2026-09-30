import java.util.*;

public final class OrderStateRepo {
    private final Map<String, OrderState> rows = new HashMap<>();

    public synchronized OrderState getOrCreate(String orderId) {
        return rows.computeIfAbsent(orderId, OrderState::new);
    }

    public synchronized OrderState get(String orderId) {
        return rows.get(orderId);
    }
}
