# Task: produce a safe rolling-release plan

A checkout platform is moving customer identity, event, cache, and persistence
contracts in one release train. The proposed rollout has repeatedly passed local
component checks but failed under mixed-version production traffic and rollback.

Inspect the repository context and produce the minimal safe rollout sequence in
`DECISION.json`.

Requirements:

- rolling deploy: v1 and v2 instances overlap;
- rollback to v1 must remain safe until the rollback window is explicitly closed;
- live writes continue during migration;
- event delivery is at-least-once and consumers roll independently;
- cache compatibility must survive mixed v1/v2 writers;
- do not solve the rollout by pausing traffic, flushing all cache, or restarting everything;
- choose only actions listed in `actions.json`;
- every chosen action may appear at most once.

The black-box `validate` tool simulates mixed-version traffic, rollback, live
backfill races, event delivery, and cache behavior. Treat its output as rollout
evidence, not as a source of implementation details. You have only a small
validation budget, so reason from the repository before probing.

`DECISION.json` format:

```json
{
  "steps": ["action_id", "..."]
}
```
