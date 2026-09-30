import java.util.*;

public final class CustomerStore {
    private final Map<Long,Customer> rows=new HashMap<>();

    public synchronized void put(Customer c){ rows.put(c.id,c); }
    public synchronized Customer get(long id){ return rows.get(id); }

    synchronized void updateLegacy(long id,String status) {
        Customer old=rows.get(id);
        Customer replacement=new Customer(id,old.stableKey,status,old.version+1);
        rows.put(id,replacement);
    }

    synchronized void updateV2(long id,String status) {
        Customer c=rows.get(id);
        c.legacyStatus=status;
        c.newStatus=status;
        c.version++;
    }

    synchronized void applyBackfill(BackfillItem captured) {
        Customer current=rows.get(captured.id());
        if (captured.capturedVersion() < current.version) return;
        current.newStatus=captured.legacyStatus();
        current.version=captured.capturedVersion();
    }
}
