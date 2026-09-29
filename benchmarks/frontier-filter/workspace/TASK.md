# Task: fix the production filter expression engine

The service uses a small filter language to decide which records enter a
workflow. The current implementation only handles simple expressions correctly.

Read `LANGUAGE.md` and the Java sources. Fix the production implementation so
it implements the complete language and error behavior.

Constraints:
- Preserve public classes and public method signatures.
- No external dependencies.
- Do not special-case visible examples.
- Malformed expressions must fail with IllegalArgumentException instead of being
  silently accepted.
- Keep the implementation reasonably small.
- Run `./run_visible_tests.sh` before finishing.
