# Refund contract

Payment refund is external. The provider is idempotent only when retries for the
same logical refund reuse one stable refund key. The process can fail after the
provider accepted a refund but before local completion is durable.
