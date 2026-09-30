# Customer read/write path

Old and new application versions overlap. Legacy writers address customers by
numeric ID; v2 reads use a stable customer key. A compatibility mapping exists
between those identities.

Strict read-after-write operations require freshly committed state. Ordinary
eventually-consistent reads may use the asynchronous replica.

Broad cache flushes are not an acceptable compatibility mechanism.
