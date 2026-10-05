# Quick monitor health signal

The quick monitor is still wasting fixed signal budget on low-information questions: a question that every monitored model repeatedly fails in the same way can remain a permanent anchor, even though an equally uninformative all-pass question is downweighted.

Update the quick-monitor health/anchor behavior so low-information extremes are handled consistently and the fixed core better reflects the monitor's real reasoning, instruction-following, and coding use. Preserve deterministic weighted selection, existing history compatibility, and the current report/config interfaces.

Validate the behavior rather than only changing labels.
