# Scheduler specification

`Scheduler.plan(tasks, workerCount)` returns one ScheduleEntry per task.

Rules:
1. Tasks are non-preemptive and have positive integer durations.
2. A task may start only after every named dependency has finished.
3. At most `workerCount` tasks may run at once.
4. Tasks with `needsGpu=true` share one exclusive GPU; two GPU tasks may not overlap.
5. Start times are non-negative integers.
6. The schedule must minimize the overall makespan.
7. If several schedules have the same minimum makespan, choose the one whose
   vector of start times is lexicographically smallest when tasks are ordered by
   task ID ascending.
8. Worker IDs are not part of optimality. After start times are fixed, assign
   each task the lowest-numbered worker that is free for the task's entire
   interval; worker numbering starts at 0.
9. Unknown dependencies, duplicate task IDs, non-positive durations, or
   workerCount <= 0 are invalid input and must throw IllegalArgumentException.
10. A dependency cycle must throw IllegalArgumentException.

The input list order must not affect the result.
