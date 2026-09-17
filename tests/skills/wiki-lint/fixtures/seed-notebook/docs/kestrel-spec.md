# Kestrel specification (canon)

This file is the canon source for Kestrel's delivery behaviour. The wiki summarises it.

## Delivery modes

Kestrel defines FOUR delivery modes:

1. `immediate` — hand to a consumer as soon as one is free.
2. `batched` — accumulate up to the batch size, then hand over.
3. `deferred` — hold until the consumer asks.
4. `replay` — re-deliver an acknowledged message on request, added in 4.2.

## Retention

An undelivered message is held for 14 days, then dropped.
