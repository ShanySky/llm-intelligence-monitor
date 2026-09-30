# Task: separate application core signal from broad coverage

The application benchmark currently aggregates every task into one quality score.
That makes stable high-information tasks indistinguishable from coverage tasks that
are intentionally retained even when current models often saturate them.

Update the existing result summarizer so the report keeps the overall quality
score but also exposes a Core Signal computed only from manifest entries whose
role is `core`.

The JSON summary must make it possible to audit:
- core quality and practical score;
- how much configured core weight was actually observed;
- whether all configured core data is present;
- whether the configured minimum number of core families exists.

The Markdown report must show each task's role and show Core Signal separately
from Overall quality. Preserve existing CLI arguments and existing overall
metrics. Make the smallest complete change and validate it with focused fixtures.
