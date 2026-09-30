# Frontier Effort Analysis

| Effort | Trials | Quality mean | Quality stddev | Runtime avg | Shell avg | Probes avg | Probe attempts avg | Total tokens avg | Reasoning avg | Saturated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| medium | 3 | 96.7 | 4.7 | 39s | 4.3 | 0.0 | 0.0 | 7012 | 123 | no |
| high | 3 | 100.0 | 0.0 | 50s | 5.7 | 0.0 | 0.0 | 9644 | 207 | no |
| xhigh | 3 | 100.0 | 0.0 | 40s | 4.7 | 0.0 | 0.0 | 8213 | 224 | no |

**M→XH classification:** `quality-ceiling-no-m-to-xh-signal`

Quality gain: 3.3 points; runtime improvement: -2.5%; shell improvement: -7.7%; probe improvement: -%; token improvement: -17.1%; paired trials: 3.

> Directional quality improvement, generic effort sensitivity, efficiency, and non-monotonic anomalies are separate signals. Effort sensitivity means the chosen effort level reliably changes quality; it does not imply that higher effort is better. Formal effort-discriminator promotion still requires repeated positive Medium→X High quality gain.
