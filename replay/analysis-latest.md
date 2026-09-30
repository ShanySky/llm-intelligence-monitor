# Frontier Effort Analysis

Trial mode: variants

| Effort | Trials | Quality mean | Quality stddev | Runtime avg | Shell avg | Probes avg | Patch files | Patch lines | Total tokens avg | Reasoning avg | Saturated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| medium | 3 | 66.2 | 26.4 | 451s | 10.0 | 0.0 | 1.3 | 86.0 | 83693 | 236 | no |
| high | 3 | 34.7 | 34.9 | 480s | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | no |
| xhigh | 3 | 64.7 | 39.2 | 480s | 0.0 | 0.0 | 0.0 | 0.0 | 0 | 0 | no |

**M→XH classification:** `needs-more-data`

Quality gain: -1.5 points; runtime improvement: -6.4%; shell improvement: 100.0%; probe improvement: -%; token improvement: 100.0%; paired trials: 3.

**Effort sensitivity:** `effort-sensitivity-confirmed` (spread 31.5 points; best=medium; worst=high; shape=nonmonotonic).

**Non-monotonic signal:** `nonmonotonic-effort-anomaly-candidate` (high-dip, 30.0 points).

**Promotion recommendation:** `effort-sensitivity-confirmed`.

> Directional quality improvement, generic effort sensitivity, efficiency, and non-monotonic anomalies are separate signals. Effort sensitivity means the chosen effort level reliably changes quality; it does not imply that higher effort is better. Formal effort-discriminator promotion still requires repeated positive Medium→X High quality gain.
