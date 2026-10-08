# Real Repo Replay Family

| Case | Effort | Replay quality | Behavior | Patch quality | Runtime | Changed files | Changed lines |
|---|---|---:|---:|---:|---:|---:|---:|
| core-signal-summary | high | 45 | 45 | - | 124s | 1 | 50 |
| repeat-sample-policy | high | 25 | 25 | - | 214s | 1 | 54 |
| quick-monitor-floor-health | high | 100 | 100 | 100 | 113s | 2 | 18 |

## Luna High screening decisions

| Case | Score | Seconds | Decision |
|---|---:|---:|---|
| core-signal-summary | 45 | 124 | effort-calibration-candidate |
| repeat-sample-policy | 25 | 214 | effort-calibration-candidate |
| quick-monitor-floor-health | 100 | 113 | coverage-only-ceiling |

> Screening is not effort confirmation; Sol M/H/XH only follows valid non-ceiling signal.
