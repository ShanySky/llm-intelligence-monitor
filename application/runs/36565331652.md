# Application Benchmark

| Task | Family | Weight | medium | xhigh |
|---|---|---:|---:|---:|
| micro-plan | solution_design | 25 | 100 (56s) | 100 (62s) |
| micro-export | coding_long_horizon | 35 | 100 (89s) | 100 (162s) |
| micro-review | code_review | 20 | 80 (100s) | 0 (480s) |
| micro-incident | agent_tool_use | 20 | 90 (480s) | 20 (480s) |

## Weighted totals

| Effort | Score | Runtime | Input tokens | Reasoning tokens |
|---|---:|---:|---:|---:|
| medium | 94.0 | 725s | 42,927 | 2,678 |
| xhigh | 64.0 | 1184s | 33,903 | 5,734 |

> Scores are objective hidden-checkpoint scores. Runtime is agent execution time, not total GitHub job time.
