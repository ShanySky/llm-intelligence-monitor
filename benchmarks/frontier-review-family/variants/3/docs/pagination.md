# Feed pagination contract
Rows are ordered by (created_at DESC, id DESC). A resumed traversal must not duplicate
or lose rows when timestamps tie, and must remain pinned to the snapshot visible when
the traversal started even while new rows arrive.
