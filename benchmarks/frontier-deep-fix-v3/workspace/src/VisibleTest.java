import java.math.BigDecimal;
import java.util.*;

public final class VisibleTest {
    public static void main(String[] args) throws Exception {
        class Repo implements ProductRepository {
            ProductSnapshot row = new ProductSnapshot(1, 1, new BigDecimal("10.00"));
            public ProductSnapshot find(long id) { return row; }
            public boolean updateIfVersion(long id,long expected,BigDecimal price) {
                if (row.version()!=expected) return false;
                row = new ProductSnapshot(id, expected+1, price);
                return true;
            }
        }
        Repo repo = new Repo();
        List<AuditWork> audit = new ArrayList<>();
        PriceService prices = new PriceService(repo, id -> {}, audit::add);
        prices.changePrice(1, 1, new BigDecimal("12.00"));
        if (!repo.find(1).price().equals(new BigDecimal("12.00"))) throw new AssertionError();
        if (audit.size()!=1) throw new AssertionError();

        System.out.println("VISIBLE_TEST_PASS");
    }
}
