# Frontier Cross-Model Validation

Task: hard-incident

| Model | Effort | Trials | Scores | Mean | Stddev | Avg runtime | Avg total tokens |
|---|---|---:|---|---:|---:|---:|---:|
| gpt-5.6-sol | xhigh | 2 | 80, 90 | 85.0 | 5.0 | 72.0s | 14128 |
| gpt-6-astra | xhigh | 2 | 100, 100 | 100.0 | 0.0 | 65.5s | 10068 |
| gpt-6-luna | xhigh | 2 | 100, 100 | 100.0 | 0.0 | 43.0s | 8250 |
| gpt-6-sol | xhigh | 2 | 100, 100 | 100.0 | 0.0 | 41.0s | 7762 |

- Model spread: 15.0 points
- All configs stable (stddev <= 12): yes
