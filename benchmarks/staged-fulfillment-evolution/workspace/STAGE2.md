# Stage 2: multi-item rollout gate

A new rollout gate has exposed an additional compatibility case. New repository
evidence is now present.

One order version can contain multiple independent line items, and every line item
must receive its own logical inventory reservation. Reproduce the newly visible
failure and refine the Stage 1 repair without losing crash/retry safety.

Run the newly available Stage 2 check before finishing.
