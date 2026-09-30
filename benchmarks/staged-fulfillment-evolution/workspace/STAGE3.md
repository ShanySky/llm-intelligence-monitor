# Stage 3: provider redelivery identity

The multi-item gate now passes. A final rollout gate reveals that the payment
provider may redeliver the same logical fulfillment under a different delivery
event ID.

Different event IDs for the same order version + line item must converge to one
local fulfillment and one external reservation. Different order versions must
remain distinct.

Use the new evidence, revise any delivery-scoped state identity that is too
narrow, and preserve all prior behavior. Run the Stage 3 check and the original
visible test before finishing.
