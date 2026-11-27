# feature: emergency (mobile) — SOS

The one-tap lifeline. Scope:

- SOS trigger flow (hold-to-confirm), note + photo attachment
- sends SOS as an HTTP POST with an Idempotency-Key via `@rescuevision/api`, queued offline and shown as not sent until the server confirms (M2)
- escalation state machine (triggered → acknowledged by command → resolved)
- "share my location" request handling when command asks for a fix

Must remain usable with one hand, poor connectivity (queue + retry), and no
attention. Everything here is designed worst-case-first.
