public interface AuditQueue {
    void enqueue(AuditWork work);
}
