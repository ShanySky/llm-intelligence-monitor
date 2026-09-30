# Task: make variant-family effort confirmation use explicit counts

The effort analyzer supports two meanings of "trial": repeated samples of one
task, and distinct variants of one task family. Variant-family promotion policy
is discrete: at least three paired variants must exist and at least two variants
must each show the configured positive quality gain.

The current implementation derives confirmation from a floating consistency
ratio. With three variants, two positives can be rejected by a threshold such as
0.67 even though the policy means "2 of 3".

Update the analyzer so variant mode uses explicit policy-driven counts and gain
thresholds, while ordinary repeat mode keeps its existing rate/min-repeat
semantics. Include enough machine-readable evidence in the JSON result to audit
the promotion decision.

Preserve existing CLI/report behavior outside this correction. Implement the
minimal complete fix and validate it with focused fixtures.
