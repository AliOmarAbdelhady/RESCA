# RescueVision: the vision

*Draft of the one-page vision statement for the repository root. Intended length: one page.*

## One sentence

RescueVision turns drone and satellite imagery, field reports and citizen requests into **one shared, live picture of a disaster** that several agencies act on together, with **AI that proposes and people who decide**, on hardware that any agency can afford.

## The problem

After an earthquake or a flood, Government, Police, EMS and Fire each look at their own map, their own radio traffic and their own list of tasks. Imagery arrives within hours, but turning it into decisions takes days, and the answers sit in files that only one agency sees. Meanwhile the lethal dangers are often combinations: flood water is a nuisance until it touches a live power line.

AI for reading disaster imagery already exists. What is missing is the chain from a pixel to a safe action that several agencies can trust, check and share.

## The story: one chain, and every feature is a link in it

| Link | What happens | Features |
| --- | --- | --- |
| **See** | Drone and satellite imagery becomes one georeferenced map of the incident. | Imagery intake, stitching, 2D and 3D map |
| **Understand what happened** | Every building gets a damage grade and an indicative restoration cost. | Damage and cost assessment |
| **Find people** | Visible and partly visible people are detected, tracked and placed on the map with an uncertainty radius. | Person detection and tracking |
| **Hear people** | Citizens ask for help with a phone number and a one-time code. | Citizen channel |
| **Understand danger** | Hazards and infrastructure are combined: flood water near a live line becomes an Electrified Water alert that closes roads and warns responders. | Compound hazard alerts |
| **Move safely** | Routes avoid closed, flooded or unverified roads for the vehicle that is driving them. | Mapping and routing |
| **Act together** | One incident, agencies that join it, missions, and a field app that works without coverage. | Incidents, missions, field app |
| **Tell and learn** | Reports freeze the facts, reviews correct the AI, and every correction feeds the next model version. | Reports, review, retraining |

**The pivot of the product is the assistance case.** It is the one thing that an AI detection, a citizen request and a responder's report all become. Everything else serves it: the map locates it, routing reaches it, hazard alerts protect the way there, and reports count it.

## The distinctive idea

Danger is recorded as **facts in space** (a flood polygon, a power asset, a road segment) and combined by **rules that are data**. The flagship rule is Electrified Water. The rule engine is:

- **cautious**: a power asset whose state is unknown is treated as live;
- **explainable**: every alert names the hazard and the asset that caused it;
- **reversible**: resolving an alert reopens the roads it closed, unless another alert still needs them closed;
- **fast and whole**: alert, road closures, route invalidation and warnings happen in one database transaction;
- **testable**: a dry-run mode answers "what if this substation floods?" without changing anything.

This is the project's real contribution: not another damage map, but a step from *seeing* to *acting safely*.

## Five principles

1. **One incident, one truth.** One database, one incident record, access decided inside the database.
2. **AI proposes, people decide.** Every AI result carries a review state. Only a person confirms a person, closes a case or dispatches a team.
3. **Uncertainty is shown, never hidden.** Confidence, age and position error travel with every result into the interface and into routing.
4. **It runs where the disaster is.** A single server without a GPU, a field app that works offline, warnings and reports in Arabic and English.
5. **Documents cannot drift from the code.** People and AI coding agents build from the same documents, and a check fails when the two disagree.

## What success looks like

- A demonstration on one ordinary server, for one user at a time, that replays a recorded incident from imagery to an Electrified Water alert.
- Measured evidence for every claim: alert-path latency, agreement between AI and human review, bytes sent per person found, CPU latency per model.
- A repository where a new contributor, human or agent, can make a working change on the first day.

## What RescueVision is not

It is a decision-support platform, not a certified safety system. It does not fly drones or switch the power network. It does not identify people. It does not promise to see through rubble.
