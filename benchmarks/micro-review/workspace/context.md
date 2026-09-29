# Context

- Spring Boot service, four instances.
- `changePrice` is transactional.
- Product reads use cache-aside: a cache miss reads committed DB state and repopulates the cache.
- Audit delivery may be retried by infrastructure and must not create duplicate business audit events.
- The goal of the patch is to make audit delivery asynchronous and keep price cache contents consistent with committed DB state.
