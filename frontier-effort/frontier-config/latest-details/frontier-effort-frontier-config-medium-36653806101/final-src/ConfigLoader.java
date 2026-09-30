import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;

public final class ConfigLoader {
    public Config load(Path file, Map<String,String> env) {
        Config cfg = new Config("INFO", 8080);

        if (file != null && Files.exists(file)) {
            Properties p = new Properties();
            try (var in = Files.newInputStream(file)) {
                p.load(in);
            } catch (IOException e) {
                throw new IllegalArgumentException("cannot load config", e);
            }

            if (p.getProperty("version") != null) {
                cfg.setVersion(p.getProperty("version").trim());
            }
            if (p.getProperty("logLevel") != null) {
                cfg.setLogLevel(p.getProperty("logLevel").trim());
            }
            if (p.getProperty("port") != null) {
                cfg.setPort(parsePort(p.getProperty("port")));
            }
        }

        String overrideVersion = env.get("APP_VERSION");
        if (overrideVersion != null) {
            cfg.setVersion(overrideVersion.trim());
        }
        if (env.get("APP_LOG_LEVEL") != null) {
            cfg.setLogLevel(env.get("APP_LOG_LEVEL").trim());
        }
        if (env.get("APP_PORT") != null) {
            cfg.setPort(parsePort(env.get("APP_PORT")));
        }

        validate(cfg);
        return cfg;
    }

    private int parsePort(String raw) {
        try {
            return Integer.parseInt(raw.trim());
        } catch (RuntimeException e) {
            throw new IllegalArgumentException("invalid port: " + raw, e);
        }
    }

    private void validate(Config cfg) {
        if (!"1.0".equals(cfg.version())) {
            throw new IllegalArgumentException("unsupported version: " + cfg.version());
        }
        if (cfg.logLevel() == null || cfg.logLevel().isBlank()) {
            throw new IllegalArgumentException("logLevel");
        }
        if (cfg.port() < 1 || cfg.port() > 65535) {
            throw new IllegalArgumentException("port");
        }
    }
}
