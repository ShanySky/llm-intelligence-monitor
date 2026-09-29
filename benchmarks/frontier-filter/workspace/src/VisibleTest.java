import java.util.*;

public final class VisibleTest {
    public static void main(String[] args) {
        FilterEngine e = new FilterEngine();
        Map<String,String> r = new HashMap<>();
        r.put("role", "admin");
        r.put("active", "yes");

        check(e.matches("role = \"admin\" AND active = \"yes\"", r));
        check(!e.matches("role = \"user\" OR active = \"no\"", r));
        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
