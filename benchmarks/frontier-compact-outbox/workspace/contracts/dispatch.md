# Dispatch contract

The order record and its pending delivery marker must become durable together, before any network send. If a process dies or a bus send fails, a later drain must find the marker. A successful send can happen immediately before the marker acknowledgement fails.

One order id corresponds to one externally visible fulfillment. Repeating an already delivered event is permitted internally only if the transport-level identity prevents a second external effect.
