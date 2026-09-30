# Task: separate model-core and effort-core maturity

The application benchmark currently reports a single combined Core maturity.
That hides an important distinction: we may already have enough stable task
families to compare models while still lacking a confirmed reasoning-effort
family.

Update application discrimination reporting so that Model Core and Effort Core
have independent configured thresholds and independent confirmed-task lists.
Overall application maturity must require both to be mature.

Model Core should count confirmed core tasks in the final application manifest.
Effort Core should count confirmed effort-family evidence from the frontier
registry. Keep the existing task-level discrimination output and CLI compatible,
and expose the split in both JSON and Markdown.

Make the smallest complete change and validate it with focused fixtures.
