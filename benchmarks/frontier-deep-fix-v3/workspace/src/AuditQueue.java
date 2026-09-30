public interface AuditQueue {
    /**
     * Queues asynchronous audit work. Delivery may be retried and may happen
     * after later product writes have already committed.
     */
    void enqueue(AuditWork work);
}
