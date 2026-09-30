public final class VisibleTest {
    public static void main(String[] args) {
        OrderStore store = new OrderStore();
        V2OrderService v2 = new V2OrderService(store);

        v2.writeStatus("order-visible", "PAID", "card");
        if (!"PAID".equals(v2.readStatus("order-visible"))) {
            throw new AssertionError("v2 happy path");
        }

        V1OrderService v1 = new V1OrderService(store);
        v1.writeStatus("old-order", "NEW");
        if (!"NEW".equals(v2.readStatus("old-order"))) {
            throw new AssertionError("v2 must read legacy-only rows");
        }

        v2.writeStatus("old-order", "PAID", "card");
        if (!"PAID".equals(v1.readStatus("old-order"))) {
            throw new AssertionError("v1 must see v2 writes");
        }

        v1.writeStatus("old-order", "SHIPPED");
        if (!"SHIPPED".equals(v2.readStatus("old-order"))) {
            throw new AssertionError("v2 must see subsequent v1 writes");
        }

        BackfillJob backfill = new BackfillJob(store);
        v1.writeStatus("migration", "NEW");
        BackfillItem snapshot = backfill.plan("migration");
        backfill.apply(snapshot);
        if (!"NEW".equals(v2.readStatus("migration"))
                || !"backfill".equals(store.get("migration").statusReason)) {
            throw new AssertionError("backfill must migrate current legacy rows");
        }

        v1.writeStatus("migration", "PAID");
        backfill.apply(snapshot);
        if (!"PAID".equals(v2.readStatus("migration"))) {
            throw new AssertionError("stale backfill must not overwrite v1");
        }

        BackfillItem nextSnapshot = backfill.plan("migration");
        v2.writeStatus("migration", "SHIPPED", "live");
        backfill.apply(nextSnapshot);
        if (!"SHIPPED".equals(v2.readStatus("migration"))
                || !"live".equals(store.get("migration").statusReason)) {
            throw new AssertionError("stale backfill must not overwrite v2");
        }

        System.out.println("VISIBLE_TEST_PASS");
    }
}
