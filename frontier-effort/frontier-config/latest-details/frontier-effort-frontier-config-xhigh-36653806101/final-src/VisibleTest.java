import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public final class VisibleTest {
    public static void main(String[] args) throws Exception {
        Path p = Files.createTempFile("frontier-config-visible", ".properties");
        try {
            ConfigLoader loader = new ConfigLoader();
            Files.writeString(p, "logLevel=DEBUG\nport=9000\n");

            Config c = loader.load(p, Map.of("APP_PORT", "9001"));
            check("1.0".equals(c.version()));
            check("DEBUG".equals(c.logLevel()));
            check(c.port() == 9001);

            Files.writeString(p, "version=1.0\nport=9000\n");
            check("1.0".equals(loader.load(p, Map.of()).version()));
            check("1.0".equals(loader.load(p, Map.of("APP_VERSION", "1.0")).version()));
            expectInvalidVersion(loader, p, Map.of("APP_VERSION", "2.0"));
            expectInvalidVersion(loader, p, Map.of("APP_VERSION", ""));

            Files.writeString(p, "version=2.0\n");
            expectInvalidVersion(loader, p, Map.of());
            check("1.0".equals(loader.load(p, Map.of("APP_VERSION", "1.0")).version()));
            Files.writeString(p, "version=2.0\nport=invalid\n");
            expectInvalidVersion(loader, p, Map.of());
        } finally {
            Files.deleteIfExists(p);
        }
        System.out.println("VISIBLE_TEST_PASS");
    }

    private static void expectInvalidVersion(ConfigLoader loader, Path p, Map<String,String> overrides) {
        try {
            loader.load(p, overrides);
            throw new AssertionError("unsupported version accepted");
        } catch (IllegalArgumentException expected) {
            check(expected.getMessage().contains("version"));
        }
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
