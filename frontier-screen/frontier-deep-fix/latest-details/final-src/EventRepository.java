public interface EventRepository {
    boolean exists(String eventId);
    void insert(String eventId);
}
