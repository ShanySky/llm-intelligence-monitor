import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public final class VisibleTest {
    public static void main(String[] args) throws Exception {
        Path p = Files.createTempFile("frontier-config-visible", ".properties");
        Files.writeString(p, "logLevel=DEBUG\nport=9000\n");

        Config c = new ConfigLoader().load(p, Map.of("APP_PORT", "9001"));
        check("DEBUG".equals(c.logLevel()));
        check(c.port() == 9001);

        Files.deleteIfExists(p);
        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
