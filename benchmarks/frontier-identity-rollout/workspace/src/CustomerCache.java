import java.util.*;

public final class CustomerCache {
    private final Map<String, String> data = new HashMap<>();

    public void putLegacy(long id, String value) {
        data.put("customer:" + id, value);
    }

    public void putV2(String customerKey, String value) {
        data.put("customer-key:" + customerKey, value);
    }

    public String getV2(String customerKey) {
        return data.get("customer-key:" + customerKey);
    }

    public String getCompatible(long legacyId, String customerKey) {
        return getV2(customerKey);
    }

    public int size() {
        return data.size();
    }
}
