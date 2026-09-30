import java.util.*;

public final class CustomerStore {
    private final Map<Long,Customer> rows=new HashMap<>();
    public void put(Customer c){ rows.put(c.id,c); }
    public Customer get(long id){ return rows.get(id); }
}
