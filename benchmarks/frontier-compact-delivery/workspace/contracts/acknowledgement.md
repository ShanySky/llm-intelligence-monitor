# Checkpoint and failure contract

Each partition has a monotonic acknowledged offset. Checkpointing means the logical effect is durably recoverable; a transient send exception must not acknowledge the offset, even when the sink might already have applied an effect. On replay, an earlier successful effect should not happen twice and the checkpoint should eventually advance.

Workers may overlap, but older offsets may not regress a checkpoint. A completed later offset makes earlier replays no-ops. Different partitions must not block one another.
