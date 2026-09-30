import java.util.*;

public final class PaymentService {
    private final PaymentProvider provider;
    private final Set<String> completed = new HashSet<>();
    private final FailureInjector failure;

    public PaymentService(PaymentProvider provider, FailureInjector failure) {
        this.provider = provider;
        this.failure = failure;
    }

    public synchronized void pay(String orderId, long version, String deliveryId) {
        String operationKey = operationKey(orderId, version);
        if (completed.contains(operationKey)) return;
        provider.charge(operationKey, orderId, version);
        failure.afterCharge();
        completed.add(operationKey);
    }

    private static String operationKey(String orderId, long version) {
        // Delivery IDs identify transport attempts. The provider key must instead
        // identify the business operation, consistently across redeliveries.
        String orderPart = orderId == null ? "-1:" : orderId.length() + ":" + orderId;
        return "payment:v1:" + orderPart + ":" + version;
    }
}
