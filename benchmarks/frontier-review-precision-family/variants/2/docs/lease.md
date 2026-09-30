# Lease contract

Every acquisition increments an immutable epoch. Renewal and completion are valid
only for the current owner+epoch pair. A paused holder may resume after expiry and
takeover; owner strings are diagnostic labels, not fencing tokens.
