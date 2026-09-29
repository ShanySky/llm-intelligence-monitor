# Application Benchmark

| Task | Family | Weight | gpt-5.6-sol / xhigh | gpt-6-astra / xhigh | gpt-6-luna / xhigh | gpt-6-sol / medium | gpt-6-sol / high | gpt-6-sol / xhigh |
|---|---|---:|---|---|---|---|---|---|
| hard-plan | solution_design | 20 | 88 / 完成 / 142s | 100 / 完成 / 149s | 100 / 完成 / 100s | 100 / 完成 / 42s | 100 / 完成 / 42s | 100 / 完成 / 58s |
| hard-webhook | coding_idempotency | 25 | 100 / 完成 / 131s | 100 / 完成 / 180s | 100 / 完成 / 92s | 100 / 完成 / 71s | 100 / 完成 / 74s | 100 / 完成 / 115s |
| hard-review | code_review | 20 | 100 / 完成 / 178s | 15 / 完成 / 271s | 85 / 完成 / 158s | 85 / 完成 / 82s | 100 / 完成 / 76s | 100 / 完成 / 127s |
| hard-incident | agent_tool_use | 15 | 90 / 完成 / 80s | 100 / 完成 / 64s | 100 / 完成 / 46s | 100 / 完成 / 49s | 90 / 完成 / 35s | 100 / 完成 / 44s |
| micro-export | coding_long_horizon_recovery | 20 | 100 / 完成 / 271s | 100 / 完成 / 439s | 100 / 完成 / 140s | 100 / 完成 / 89s | 100 / 完成 / 100s | 100 / 完成 / 127s |

## Overall

| Model | Effort | Quality | Budget completion | Practical | Runtime | Avg/task | Input tokens | Reasoning tokens | Data |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-5.6-sol | xhigh | 96.1 | 100% | 96.7 | 802s | 160s | 185,778 | 19,042 | 完整 |
| gpt-6-astra | xhigh | 83.0 | 100% | 85.5 | 1103s | 221s | 188,093 | 14,452 | 完整 |
| gpt-6-luna | xhigh | 97.0 | 100% | 97.5 | 536s | 107s | 123,886 | 9,209 | 完整 |
| gpt-6-sol | medium | 97.0 | 100% | 97.5 | 333s | 67s | 64,384 | 3,173 | 完整 |
| gpt-6-sol | high | 98.5 | 100% | 98.7 | 327s | 65s | 63,077 | 4,430 | 完整 |
| gpt-6-sol | xhigh | 100.0 | 100% | 100.0 | 471s | 94s | 108,296 | 7,614 | 完整 |

> Quality = hidden-checkpoint score. Practical = 85% quality + 15% budget-completion reliability. Runtime and token usage are reported separately and are not silently folded into intelligence quality. Infrastructure/API failures are marked incomplete instead of being scored as model failures.
