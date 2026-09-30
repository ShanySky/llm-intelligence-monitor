public interface EventRepository {
    /**
     * eventId identifies one provider delivery. Different event IDs may still
     * describe the same logical order/version.
     */
    boolean exists(String eventId);
    void insert(String eventId);
}
