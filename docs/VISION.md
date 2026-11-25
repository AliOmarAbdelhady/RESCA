# Vision

RESCA (Real-time Emergency Sensing, Coordination & Assessment) gives every agency in a disaster one shared, live picture: what is damaged, where people need help, which roads are safe, and which hazards are forming. It turns drone and satellite imagery into decisions a person confirms.

This is a graduation project built to the standard of a national emergency system: security, correctness and honest limits come before features.

## Users

| Who | Role in the system | Main need |
|---|---|---|
| Commander (government) | `COMMANDER` | Overview of the incident, agencies, alerts and decisions |
| Analyst | `ANALYST` | Imagery, damage assessment review, reports |
| Field responder (police, EMS, fire) | `FIELD_RESPONDER` | Missions, safe routes, reporting hazards and people, SOS, offline use |
| Agency administrator | `AGENCY_ADMIN` | Users, teams and vehicles of one agency |
| Citizen | citizen channel | Ask for help and share photos, with phone verification |

Agencies are `GOVERNMENT`, `POLICE`, `EMS` and `FIRE`; several agencies share one incident. Each agency and role sees the same pages arranged and coloured for its job (DEC-12).

## Features

| # | Feature | In the demo |
|---|---|---|
| F1 | Building damage assessment and repair-cost ranges from before/after imagery | Yes, on prepared imagery |
| F2 | 2D/3D maps and road damage, with safe routing | 2D live, 3D precomputed |
| F3 | Detecting people in aerial images, including partly visible | Proposed until a model passes A3 |
| F4 | Tracking people across frames and opening assistance cases | Proposed until a model passes A3 |
| F5 | Compound hazards, such as flood water near live power ("electrified water"), with alerts and re-routing | Yes (database engine) |
| F6 | Reports, historical case search and a read-only assistant | Reports yes; assistant proposed |

## Principles

1. A person confirms every consequential AI result.
2. Nothing is lost: offline actions are queued, retried safely and shown as unsent until confirmed.
3. Every agency sees only what it is allowed to see, enforced in the database.
4. It works on one CPU server with no budget; heavy work is prepared in advance.
5. The report and the UI label what is proposed versus demonstrated.

## Out of scope

GPUs in production, Kubernetes, message brokers, CRDT sync, mesh radio networks, live drone video, server-side 3D reconstruction, any language model on the server.
