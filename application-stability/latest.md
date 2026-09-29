# Application Stability Validation

Task: hard-review

| Model | Effort | Trials | Scores | Mean | Stddev | Avg runtime | Avg input tokens | Avg reasoning tokens | Stable |
|---|---|---:|---|---:|---:|---:|---:|---:|:---:|
| gpt-5.6-sol | xhigh | 1 | 100 | 100.0 | 0.0 | 178s | 52,590 | 4,418 | 是 |
| gpt-6-astra | xhigh | 3 | 15, 100, 100 | 71.7 | 40.1 | 224s | 48,379 | 1,810 | 否 |
| gpt-6-luna | xhigh | 1 | 85 | 85.0 | 0.0 | 158s | 51,706 | 1,794 | 是 |
| gpt-6-sol | medium | 3 | 85, 65, 100 | 83.3 | 14.3 | 89s | 17,472 | 432 | 否 |
| gpt-6-sol | high | 3 | 100, 85, 85 | 90.0 | 7.1 | 78s | 13,830 | 829 | 是 |
| gpt-6-sol | xhigh | 3 | 100, 85, 85 | 90.0 | 7.1 | 114s | 32,217 | 962 | 是 |

- Sol effort spread: 6.7 points
- X High model spread (tested configs): 28.3 points
- All tested configs stable (stddev <= 12): no
