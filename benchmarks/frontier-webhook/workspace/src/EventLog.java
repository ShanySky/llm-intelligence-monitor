import java.util.*;

public final class EventLog {
    private final Set<String> ids = new HashSet<>();

    public boolean record(String eventId) {
        return ids.add(eventId);
    }

    public boolean contains(String eventId) {
        return ids.contains(eventId);
    }

    public int size() {
        return ids.size();
    }
}
