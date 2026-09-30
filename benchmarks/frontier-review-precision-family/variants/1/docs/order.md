# Order confirmation contract

Each accepted order version is a distinct logical confirmation. Order state and its
outbox record are committed atomically in one database transaction.

The outbox publisher is at-least-once. Its sink deduplicates by the supplied
business operation key, so retries for one logical confirmation must reuse that
key while different accepted versions must remain distinct.
