# Verification cache contract
Different issuers may reuse the same kid. Key material may be replaced under the same
issuer+kid; registry revision identifies the material generation. Cache hits must
therefore preserve both identity scope and registry freshness.
