# Frontier Effort Analysis

Trial mode: variants

| Effort | Trials | Quality mean | Quality stddev | Runtime avg | Shell avg | Probes avg | Patch files | Patch lines | Total tokens avg | Reasoning avg | Saturated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| medium | 2 | 62.5 | 37.5 | 406s | 9.0 | 0.0 | 0.5 | 22.0 | 39607 | 225 | yes |
| high | 2 | 60.5 | 35.5 | 365s | 18.0 | 0.0 | 2.5 | 135.5 | 267102 | 1158 | yes |
| xhigh | 2 | 25.0 | 0.0 | 400s | 11.5 | 0.0 | 1.5 | 50.0 | 190614 | 2532 | yes |

**M→XH classification:** `budget-confounded`

Quality gain: -37.5 points; runtime improvement: 1.5%; shell improvement: -27.8%; probe improvement: -%; token improvement: -381.3%; paired trials: 2.

**Effort sensitivity:** `effort-sensitivity-candidate` (spread 37.5 points; best=medium; worst=xhigh; shape=nonincreasing).

**Promotion recommendation:** `do-not-promote`.

> Directional quality improvement, generic effort sensitivity, efficiency, and non-monotonic anomalies are separate signals. Effort sensitivity means the chosen effort level reliably changes quality; it does not imply that higher effort is better. Formal effort-discriminator promotion still requires repeated positive Medium→X High quality gain.
