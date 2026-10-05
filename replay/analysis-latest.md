# Frontier Effort Analysis

Trial mode: variants

| Effort | Trials | Quality mean | Quality stddev | Runtime avg | Shell avg | Probes avg | Patch files | Patch lines | Total tokens avg | Reasoning avg | Saturated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| medium | 3 | 59.3 | 35.0 | 395s | 20.3 | 0.0 | 2.0 | 79.0 | 186352 | 528 | yes |
| high | 3 | 57.9 | 33.9 | 431s | 18.7 | 0.0 | 2.0 | 111.7 | 223155 | 1436 | yes |
| xhigh | 3 | 62.0 | 36.9 | 440s | 15.3 | 0.0 | 1.0 | 38.0 | 206898 | 3588 | yes |

**M→XH classification:** `budget-confounded`

Quality gain: 2.7 points; runtime improvement: -11.3%; shell improvement: 24.6%; probe improvement: -%; token improvement: -11.0%; paired trials: 3.

**Promotion recommendation:** `do-not-promote`.

> Directional quality improvement, generic effort sensitivity, efficiency, and non-monotonic anomalies are separate signals. Effort sensitivity means the chosen effort level reliably changes quality; it does not imply that higher effort is better. Formal effort-discriminator promotion still requires repeated positive Medium→X High quality gain.
