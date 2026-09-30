import java.util.concurrent.atomic.AtomicInteger;

public final class VisibleTest {
    public static void main(String[] args) {
        Cache<String,String> cache = new Cache<>();
        AtomicInteger calls = new AtomicInteger();

        String a = cache.get("a", k -> {
            calls.incrementAndGet();
            return "A";
        });
        String b = cache.get("a", k -> {
            calls.incrementAndGet();
            return "B";
        });

        if (!"A".equals(a) || !"A".equals(b) || calls.get() != 1 || cache.size() != 1) {
            throw new AssertionError("basic caching");
        }

        System.out.println("VISIBLE_TEST_PASS");
    }
}
