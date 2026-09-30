# Feed traversal contract

Pagination uses keyset order (created_at DESC, id DESC). The first page pins a
snapshot sequence. Resumed pages must continue that same snapshot even while new
rows arrive. The tuple boundary and the snapshot are independent requirements.
