# Task: recover a delivery stream without lost or duplicated effects

A delivery processor started losing some customer side effects after transient downstream failures. Other retries produced duplicate side effects, even though each event was processed by the normal handler. A replay following a checkpoint can also regress stream progress.

Read the repository contracts and implementation across the source files. Implement the minimal complete fix, preserving public class and method signatures. The source supports concurrent workers and different delivery envelopes for the same logical event.

Run `./run_visible_tests.sh` and verify behavior after failures. Do not edit contracts, tests, or runner scripts.
