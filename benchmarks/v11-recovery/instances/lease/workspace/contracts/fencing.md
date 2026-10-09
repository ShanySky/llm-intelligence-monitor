# Lease / effect contract
- `acquire(job, owner, now, ttl)` is generation-fenced. An active lease blocks a competing acquire.
- Ownership validity requires matching job, owner, generation and unexpired deadline. An expired token cannot be renewed.
- `Worker.commit(job, owner, token, now, operation, between_check=None)` may invoke a callback that transfers ownership before the effect.
- Final ownership verification and effect application must happen together as a critical section; pre-callback checking alone is unsafe.
- Repeated work does not duplicate a business operation; unrelated jobs are isolated.
