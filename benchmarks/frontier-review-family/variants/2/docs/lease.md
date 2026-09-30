# Lease contract
A lease has a monotonically increasing epoch. After expiry, an old holder may resume
after a new holder acquired the job. Durable completion/renewal must prove the current
epoch, not merely an owner string. External publish is at-least-once and idempotent
only when one logical job reuses one stable business key.
