@Service public class PaymentService {
 @Transactional public void markPaid(String eventId,long orderId){ Order o=repo.find(orderId); o.setPaid(true); cache.evict(orderId); this.fulfillAsync(eventId,orderId); }
 @Async public void fulfillAsync(String eventId,long orderId){ Order o=repo.find(orderId); inventory.reserve(orderId,"evt:"+eventId); audit.send(new Audit(UUID.randomUUID().toString(),orderId)); }
}
