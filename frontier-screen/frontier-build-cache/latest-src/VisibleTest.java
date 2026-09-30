public final class VisibleTest {
    public static void main(String[] args) {
        Workspace ws = new Workspace();
        ws.add("app", "v1");

        BuildCache cache = new BuildCache();
        Compiler compiler = new Compiler();
        IncrementalBuilder builder = new IncrementalBuilder(ws, cache, compiler);

        Artifact a = builder.build("app");
        check(a.output().contains("v1"));
        check(compiler.buildCount("app") == 1);

        ws.updateSource("app", "v2");
        Artifact b = builder.build("app");
        check(b.output().contains("v2"));
        check(compiler.buildCount("app") == 2);

        Artifact c = builder.build("app");
        check(c.output().equals(b.output()));
        check(compiler.buildCount("app") == 2);

        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
