# Application Task Discrimination Analysis

| Task | Family | Role | Class | XHigh model spread | Sol M→XH gain | Efficiency signal | Min effort trials | Repeat stddev | Ceiling rate | Max avg runtime |
|---|---|---|---|---:|---:|---|---:|---:|---:|---:|
| hard-plan | solution_design | coverage | coverage-only-ceiling | 0.0 | 0.0 | - | 1 | 0.0 | 100% | 118s |
| hard-webhook | coding_idempotency | coverage | coverage-only-ceiling | 0.0 | 0.0 | - | 1 | 0.0 | 100% | 200s |
| frontier-review-deep | code_review_cross_file_reliability | core | model+effort-candidate | 10.0 | 15.0 | - | 1 | 0.0 | 33% | 347s |
| hard-incident | agent_tool_use | core | model-discriminator | 10.0 | -10.0 | - | 1 | 0.0 | 67% | 74s |
| micro-export | coding_long_horizon_recovery | coverage | coverage-only-ceiling | 0.0 | 0.0 | - | 1 | 0.0 | 100% | 382s |

**Core signal maturity:** 1/2 confirmed families → not yet mature.

> Selection rule: quality discrimination and execution efficiency are separate signals. Effort discrimination requires a repeated positive Medium→X High quality gain. A ceiling task may additionally show an efficiency candidate when X High uses materially less runtime/tool work/token cost at the same quality, but that does not count as a quality win and still requires repeated validation.
