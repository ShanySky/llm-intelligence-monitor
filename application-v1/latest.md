# Application Benchmark

| Task | Family | Role | Weight | gpt-5.6-sol / high | gpt-6-astra / high | gpt-6-luna / high | gpt-6.1-sol / high |
|---|---|---|---:|---|---|---|---|
| hard-plan | solution_design | coverage | 20 | - | - | - | - |
| hard-webhook | coding_idempotency | coverage | 25 | - | - | - | - |
| frontier-review-deep | code_review_cross_file_reliability | core | 20 | 90 / 完成 / 136s | 100 / 完成 / 117s | 90 / 完成 / 80s | 100 / 完成 / 188s |
| hard-incident | agent_tool_use | core | 15 | 80 / 完成 / 40s | 100 / 完成 / 43s | 90 / 完成 / 51s | 100 / 完成 / 63s |
| micro-export | coding_long_horizon_recovery | coverage | 20 | - | - | - | - |

## Overall

| Model | Effort | Overall quality | Core signal | Core mature | Budget completion | Practical | Runtime | Avg/task | Input tokens | Reasoning tokens | Data |
|---|---|---:|---:|:---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.6-sol | high | 85.7 | 85.7 | 是 | 100% | 87.9 | 176s | 88s | 23,139 | 4,852 | 不完整： |
| gpt-6-astra | high | 100.0 | 100.0 | 是 | 100% | 100.0 | 160s | 80s | 25,010 | 869 | 不完整： |
| gpt-6-luna | high | 90.0 | 90.0 | 是 | 100% | 91.5 | 131s | 66s | 36,190 | 1,814 | 不完整： |
| gpt-6.1-sol | high | 100.0 | 100.0 | 是 | 100% | 100.0 | 251s | 126s | 37,714 | 2,588 | 不完整： |

> Overall/Core quality only uses completed, non-budget-confounded tasks. Raw timed-out patch scores are diagnostic only; reliability and runtime are separate. Core maturity additionally requires all configured core tasks to have admissible outcomes. Practical combines completed quality (85%) and completion reliability (15%) on admissible samples; report data is incomplete if a task timed out.
