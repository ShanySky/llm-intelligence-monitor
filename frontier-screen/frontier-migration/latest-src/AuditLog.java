import java.util.*;

public final class AuditLog {
    private final java.util.List<String> entries = new ArrayList<>();

    public void add(String text) {
        entries.add(text);
    }

    public int size() {
        return entries.size();
    }
}
