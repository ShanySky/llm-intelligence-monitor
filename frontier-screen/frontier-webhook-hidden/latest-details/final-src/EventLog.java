import java.util.*;

public final class EventLog {
    private final Set<String> ids = new HashSet<>();

    public synchronized boolean record(String eventId) {
        return ids.add(eventId);
    }

    public synchronized boolean contains(String eventId) {
        return ids.contains(eventId);
    }

    public synchronized int size() {
        return ids.size();
    }
}
