# Task: add configuration format versioning safely

This small Java service has a repository-wide configuration contract. Add explicit
configuration format versioning so future incompatible formats can be rejected.

Requirements:

- The only supported explicit version is `1.0`.
- Existing configuration files that omit `version` must remain valid and behave
  as version `1.0`.
- An unsupported explicit version must fail fast with `IllegalArgumentException`.
- Existing environment override behavior must continue to work; the version field
  participates in the same `APP_...` override convention as other root fields.
- The JSON schema and checked-in example configs must describe the supported
  version consistently.
- Preserve existing public classes and public method signatures.
- Follow the repository's generated-file convention rather than hand-maintaining
  generated output independently.
- Do not add external dependencies.

Run both:

```
./run_visible_tests.sh
./check_generated.sh
```

before finishing.
