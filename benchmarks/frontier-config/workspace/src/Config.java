public final class Config {
    private String logLevel;
    private int port;

    Config(String logLevel, int port) {
        this.logLevel = logLevel;
        this.port = port;
    }

    public String logLevel() {
        return logLevel;
    }

    public int port() {
        return port;
    }

    void setLogLevel(String value) {
        logLevel = value;
    }

    void setPort(int value) {
        port = value;
    }
}
