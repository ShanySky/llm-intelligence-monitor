# Frontier Cross-Model Validation

Task: frontier-review-deep

| Model | Effort | Trials | Scores | Mean | Stddev | Avg runtime | Avg total tokens |
|---|---|---:|---|---:|---:|---:|---:|
| gpt-5.6-sol | xhigh | 2 | 75, 85 | 80.0 | 5.0 | 223.5s | 43839 |
| gpt-6-astra | xhigh | 2 | 100, 100 | 100.0 | 0.0 | 329.5s | 49542 |
| gpt-6-luna | xhigh | 2 | 90, 90 | 90.0 | 0.0 | 216.0s | 38622 |
| gpt-6-sol | xhigh | 2 | 85, 100 | 92.5 | 7.5 | 150.0s | 20102 |

- Model spread: 20.0 points
- All configs stable (stddev <= 12): yes
