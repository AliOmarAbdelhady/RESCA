# Person 3, Joe: Section 3.1 System Description

See the [review index](README.md) for the shared vocabulary.

Every subsection in the report is still a "[P3 · ... Status: NOT STARTED]" placeholder, and two other sections already point to it:

- Section 3.2 says the full role description is in Section 3.1.3 (the text currently says "Section 2.2", which Mahmoud will correct).
- Section 3.3 says "the products intended for each node are described in Section 3.1.5".

Figure 3-1 and Tables 3-1 and 3-2 are reserved in this section. Section 3.3 starts at Figure 3-2 and Section 3.2 at Table 3-3, so this section must contain exactly one figure and two tables, or the numbering of both later sections changes.

## What to write

| Subsection | Content | Rules |
|---|---|---|
| 3.1 introduction | Two or three sentences on what the section covers. | None |
| 3.1.1 System overview and Figure 3-1 "Proposed RESCA workflow" | What the platform is for and how a user moves from viewing an affected area to coordinating assistance: review information, view people and hazards on the map, assess, coordinate, update status. | Follow the flows of UC-01 to UC-10 in Section 3.2.3 and the architecture in Figure 3-2. Plain language, no requirement IDs needed. |
| 3.1.2 Methodology (SRS 2.1) | The proposed approach and main workflow in ordinary language. | Consistent with Figure 3-1. |
| 3.1.3 Users and Table 3-1 "User roles and privileges" (Role, Characteristics, Goals, Can view, Can change) | One row per role. | Roles exactly as Section 3.2 Table 3-5: Platform Administrator, Agency Administrator, Commander, Analyst, Field Responder, Citizen. Agencies Government, Police, EMS, Fire; agency and role are independent. An agency sees an incident only while its participation is active. Only a Commander approves reports and resolves alerts. The Platform Administrator is the only user without an agency. Hospitals are receiving facilities, and hospital coordinators are stakeholders, not users. |
| Table 3-2 "Summary of main features" (Feature, Purpose, Main users) | One row per feature. | Names exactly as Table 3-3: F1 to F6 (see the index). Main users from Table 3-5. |
| 3.1.4.1 Assumptions | Each with its consequence if wrong. | Candidates from 3.2: drone images carry GPS metadata; SMS and push services exist; a utility power-state feed is optional (manual entry otherwise, IR-SW-04); rule distances and thresholds need confirmation with civil defence and utilities; the targets in 3.2.4 are proposals. |
| 3.1.4.2 Constraints | Each with its consequence. | From Chapter 1 Table 1-8: student team, GPU access, open data, no live integration with government, hospital or dispatch systems. |
| 3.1.4.3 Limitations | Each with its consequence. | AI outputs are candidates for human review; a detection is not a confirmed person; people buried under rubble are out of scope for F3; observations may be incomplete, delayed or uncertain; an unknown power state is treated as energised; cost estimates are indicative, not engineering or insurance valuations; the platform does not fly drones or control the power network; the 3.2.4 targets are not measured results. |
| 3.1.4.4 Dependencies | Each with its consequence. | From 3.2.2.3: object storage, OpenStreetMap or Overture road data, the AI inference service, push services, an SMS gateway, the optional utility feed. |
| 3.1.5 Intended technologies (SRS 2.4) | A short agreed description of the web command console, the mobile field application and the mapping environment. | Must match Section 3.3: PostgreSQL 18 with PostGIS 3.6, pgRouting and pgvector, row-level security, object storage, WGS 84, push and SMS services. Do not write PostgreSQL 16. Describe, do not run a selection exercise. |

## Note on the work plan

The Person 3 entry in `documentation-work-plan.md` still lists "police, ambulance staff, hospital coordinators, an incident coordinator" as users. The approved design replaced this list with the roles above. Follow the design.

## Review

Yassin reviews this section. Mahmoud checks that the role and feature names match Section 3.2.
