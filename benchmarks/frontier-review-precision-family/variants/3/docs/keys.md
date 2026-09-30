# Verification cache contract

Verification key identity is issuer+kid. Registry revision identifies the key
material generation, because material may be replaced under the same issuer+kid.
A cache hit must be valid for both identity and generation.

Legacy no-kid fallback is intentionally issuer-scoped and checks only retained
overlap keys for that issuer.
