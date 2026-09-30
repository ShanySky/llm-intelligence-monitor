# Application Task Discrimination Analysis

| Task | Family | Role | Class | XHigh model spread | Sol M→XH gain | Efficiency signal | Min effort trials | Repeat stddev | Ceiling rate | Max avg runtime |
|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| hard-plan | solution_design | coverage | model-discriminator | 12.0 | -12.0 | - | 1 | 0.0 | 83% | 164s |
| hard-webhook | coding_idempotency | coverage | coverage-only-ceiling | 0.0 | 0.0 | - | 1 | 0.0 | 100% | 184s |
| frontier-review-deep | code_review_cross_file_reliability | core | model+effort-candidate | 15.0 | 10.0 | - | 1 | 0.0 | 33% | 410s |
| hard-incident | agent_tool_use | core | model-discriminator | 20.0 | 0.0 | - | 1 | 0.0 | 83% | 66s |
| micro-export | coding_long_horizon_recovery | coverage | coverage-only-ceiling | 0.0 | 0.0 | - | 1 | 0.0 | 100% | 389s |

**Core signal maturity:** 1/2 confirmed families → not yet mature.

> Selection rule: quality discrimination and execution efficiency are separate signals. Effort discrimination requires a repeated positive Medium→X High quality gain. A ceiling task may additionally show an efficiency candidate when X High uses materially less runtime/tool work/token cost at the same quality, but that does not count as a quality win and still requires repeated validation.
