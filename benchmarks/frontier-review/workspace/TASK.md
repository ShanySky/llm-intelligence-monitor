# Task: review this production patch

A team proposes the patch in this workspace for a Spring-style Java service.
Read CONTEXT.md and all Java files.

Write REVIEW.md containing only blocking correctness/reliability findings. For each
finding, explain the failure mode and give the minimal safe fix direction.

End with exactly one line:

VERDICT: APPROVE

or

VERDICT: REQUEST_CHANGES

Do not invent requirements not supported by the context. Focus on issues that can
cause incorrect business state, stale reads, duplicate external side effects, or
lost audit delivery under the documented failure model.
