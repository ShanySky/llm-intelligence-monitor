public final class CacheCompatibilityProbe {
    public static void main(String[] args) {
        CustomerCache cache = new CustomerCache();

        cache.putLegacy(12L, "legacy-value");
        check("legacy-value".equals(cache.getCompatible(12L, "ck-12")));

        cache.putV2("ck-12", "new-value");
        check("new-value".equals(cache.getCompatible(12L, "ck-12")));

        cache.invalidateLegacy(12L, "ck-12");
        check(cache.getCompatible(12L, "ck-12") == null);
        check(cache.size() == 0);

        System.out.println("CACHE_COMPATIBILITY_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError("mixed-version cache contract");
    }
}
