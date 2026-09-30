public final class StatusCodec {
    private StatusCodec() {}

    public static int toCode(String status) {
        return switch (status) {
            case "NEW" -> 0;
            case "PAID" -> 1;
            case "SHIPPED" -> 2;
            case "CANCELLED" -> 3;
            default -> throw new IllegalArgumentException("unknown status: " + status);
        };
    }

    public static String fromCode(int code) {
        return switch (code) {
            case 0 -> "NEW";
            case 1 -> "PAID";
            case 2 -> "SHIPPED";
            case 3 -> "CANCELLED";
            default -> throw new IllegalArgumentException("unknown code: " + code);
        };
    }
}
