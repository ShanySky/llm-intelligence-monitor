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
        if (completed.contains(deliveryId)) return;
        provider.charge("delivery:" + deliveryId, orderId, version);
        failure.afterCharge();
        completed.add(deliveryId);
    }
}
