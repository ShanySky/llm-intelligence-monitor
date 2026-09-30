# Task: repair resumable customer import

The importer passes its simple happy-path test, but production recovery still shows
missing or duplicated customer upserts when a job is retried while the source feed
continues to change.

The intended contract is high level:

- one import job processes the rows that existed when that job first started;
- retrying or concurrently resuming the same job must converge without duplicate
  external customer upserts;
- ordering ties in the source must not lose rows;
- completed progress must survive retries.

Inspect the repository and implement the minimal complete repair. Preserve public
class names, constructors, and existing public method signatures. Do not add
external dependencies or special-case IDs.

A black-box validation tool is available in this benchmark. Use it as engineering
evidence: fix failures, rerun validation, and continue until the implementation
converges. Also keep the visible happy path passing.
