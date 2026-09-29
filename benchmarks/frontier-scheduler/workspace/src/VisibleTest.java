import java.util.*;

public final class VisibleTest {
    public static void main(String[] args) {
        Scheduler s = new Scheduler();
        List<Task> tasks = List.of(
            new Task("A", 2, List.of(), false),
            new Task("B", 3, List.of(), false),
            new Task("C", 2, List.of("A"), false)
        );
        List<ScheduleEntry> plan = s.plan(tasks, 2);
        Map<String,ScheduleEntry> m = new HashMap<>();
        for (ScheduleEntry e : plan) m.put(e.id(), e);

        check(m.get("A").start() == 0);
        check(m.get("B").start() == 0);
        check(m.get("C").start() == 2);
        check(plan.stream().mapToInt(ScheduleEntry::end).max().orElseThrow() == 4);
        System.out.println("VISIBLE_TEST_PASS");
    }

    static void check(boolean ok) {
        if (!ok) throw new AssertionError();
    }
}
