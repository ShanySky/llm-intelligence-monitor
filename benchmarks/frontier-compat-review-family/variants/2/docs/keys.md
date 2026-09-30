# Verification key identity

A verification key is scoped by issuer and kid. Different issuers may legally reuse
the same kid. Registry revision identifies the material generation; an issuer may
replace key material under the same kid during emergency rotation.

A verifier cache hit must therefore be valid for both key identity and registry
generation.
