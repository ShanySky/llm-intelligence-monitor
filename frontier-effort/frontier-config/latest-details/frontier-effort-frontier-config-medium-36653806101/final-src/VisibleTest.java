import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public final class VisibleTest {
    public static void main(String[] args) throws Exception {
        Path p = Files.createTempFile("frontier-config-visible", ".properties");
        try {
            Files.writeString(p, "logLevel=DEBUG\nport=9000\n");
            ConfigLoader loader = new ConfigLoader();
            Config c = loader.load(p, Map.of("APP_PORT", "9001"));
            check("1.0".equals(c.version()));
            check("DEBUG".equals(c.logLevel()));
            check(c.port() == 9001);

            Files.writeString(p, "version=1.0\n");
            check("1.0".equals(loader.load(p, Map.of()).version()));
            Files.writeString(p, "version=2.0\n");
            expectInvalid(() -> loader.load(p, Map.of()));
            check("1.0".equals(loader.load(p, Map.of("APP_VERSION", "1.0")).version()));
            expectInvalid(() -> loader.load(p, Map.of("APP_VERSION", "2.0")));
            Files.writeString(p, "version=1.0\n");
            expectInvalid(() -> loader.load(p, Map.of("APP_VERSION", "2.0")));
            expectInvalid(() -> loader.load(p, Map.of("APP_VERSION", "")));
        } finally {
            Files.deleteIfExists(p);
        }
        System.out.println("VISIBLE_TEST_PASS");
    }

    static void expectInvalid(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // Unsupported versions must be rejected.
        }
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
