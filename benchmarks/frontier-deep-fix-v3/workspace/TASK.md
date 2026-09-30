# Task: repair the production reliability regression

The patch in this workspace passes its happy-path smoke test, but production
validation still reports three classes of failures:

- some concurrent price changes expose stale or incorrect externally observed state;
- payment redelivery/recovery can create duplicate business effects or fail to converge;
- paired reservation operations occasionally stall under opposing concurrent requests.

Inspect the code and the local API contracts. Implement the minimal complete
repair while preserving existing public class names, constructors, and public
method signatures. Do not add external dependencies or special-case test data.

The black-box validator reports only the broad failing subsystem. Use it as
runtime evidence, not as a checklist of exact bugs. Run `./run_visible_tests.sh`
before finishing.
