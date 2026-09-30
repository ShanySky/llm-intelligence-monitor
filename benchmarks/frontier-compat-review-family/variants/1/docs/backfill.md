# Online backfill

Backfill captures the source row version together with the legacy value. Live writes
continue while captured work is delayed. Applying an old capture after a newer live
write must not overwrite the newer representation.
