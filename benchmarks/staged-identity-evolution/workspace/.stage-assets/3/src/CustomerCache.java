import java.util.*;

public final class CustomerCache {
    private final Map<String,String> data = new HashMap<>();

    public synchronized void putLegacy(long id, String value) {
        data.put("customer:" + id, value);
    }

    public synchronized void putV2(String customerKey, String value) {
        data.put("customer-key:" + customerKey, value);
    }

    public synchronized String getCompatible(long legacyId, String customerKey) {
        return data.get("customer-key:" + customerKey);
    }

    public synchronized void invalidateLegacy(long legacyId, String customerKey) {
        data.remove("customer:" + legacyId);
    }

    public synchronized int size() {
        return data.size();
    }
}
