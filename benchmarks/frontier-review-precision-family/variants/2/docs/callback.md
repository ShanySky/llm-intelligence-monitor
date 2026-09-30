# Callback contract

Callbacks are at-least-once. One job generation is one logical callback operation.
The remote endpoint deduplicates only when retries reuse the same business key.
