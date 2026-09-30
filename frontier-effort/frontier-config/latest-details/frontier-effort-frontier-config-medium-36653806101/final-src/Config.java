public final class Config {
    private String version = "1.0";
    private String logLevel;
    private int port;

    Config(String logLevel, int port) {
        this.logLevel = logLevel;
        this.port = port;
    }

    public String version() {
        return version;
    }

    public String logLevel() {
        return logLevel;
    }

    public int port() {
        return port;
    }

    void setVersion(String value) {
        version = value;
    }

    void setLogLevel(String value) {
        logLevel = value;
    }

    void setPort(int value) {
        port = value;
    }
}
