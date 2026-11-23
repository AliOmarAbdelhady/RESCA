# Person 4, Mahmoud: Section 3.2 Requirements and Appendix C

See the [review index](README.md) for the shared vocabulary. Severity: High blocks other sections or contradicts the design; Medium affects consistency or testability; Low is polish.

Section 3.2 is in good shape. All 161 requirement IDs are unique. Every ID that Sections 3.3, Chapter 4 and Appendix C cite exists, and UC-01 to UC-10 match Section 3.3. Agency and role names match the design, and hospital coordinators are correctly treated as stakeholders. The merged 3.2 does not state a PostgreSQL version, so the PostgreSQL 16 line from your original PDF did not carry over.

## Problems

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| M1 | High | Actors: "Section 2.2 gives the full description of each role and its privileges." | Wrong cross-reference after the merge. | "Section 3.1.3". |
| M2 | High | Every requirement table | The work plan asks for "a way a future reviewer could judge whether it is met". No table has a verification method or acceptance target, and Chapter 1's SC-01 to SC-07 are never linked. | A Verification column (Test, Inspection, Demonstration, Analysis), or one rule plus a mapping to SC-01 to SC-07. |
| M3 | High | UC-06 steps 3 and 4; FR-PT-09 | Section 3.3 and the database make a case from a track start as DETECTED and require confirmation before assignment. UC-06 goes from creation straight to assignment. | Add a confirmation step and state in FR-PT-09 that only a confirmed case can be assigned. |
| M4 | High | FR-RP-04: "move each report through draft, approved and published states"; UC-08 alternative 4a | Section 3.3 Figure 3-33 and the schema have DRAFT, PENDING_APPROVAL, APPROVED, PUBLISHED, and a "request changes" path back to DRAFT. | Add the pending-approval state to FR-RP-04 and a requirement for return to draft with a comment. |
| M5 | Medium | UC-06 step 6 "mark the case rescued"; final state "The case is closed" | In the case life cycle RESCUED is not a closed state; closed states are TRANSPORTED, DECEASED and FALSE_ALARM. | Align the step and the final state. |
| M6 | Medium | UC-03 4a "records a new assessment awaiting Analyst review" vs FR-DC-07 "allow an Analyst or field responder to override a damage grade" (Actor: Analyst) | "Override" and "awaiting review" conflict. | A responder proposes and an Analyst confirms (or the reverse); fix the Actor column. |
| M7 | Medium | UC-01 step 7 "Each invited Commander accepts"; UC-09 step 1 "accepts it" | No requirement covers accepting, declining or withdrawing an incident invitation, or accepting or declining a mission assignment. The database has these states. | Add the FRs. |
| M8 | Medium | UC-10 3a "kept as unmatched and reviewed by the Platform Administrator"; 4a "may lead to the account being blocked" | No requirement covers unmatched requests or rejection with a reason. FR-FC-11 gives blocking to the Agency Administrator, but Table 3-5 does not list that duty. | Add the requirements and update Table 3-5. |
| M9 | Medium | NFR-MT-01 (Must) "Hazard rules, cost profiles, roles and permissions shall be editable as data" vs FR-HZ-13 and FR-DC-09 (Should) | The same capability has two priorities. No actor edits roles and permissions. | One priority; name who edits roles and permissions, or drop that part. |
| M10 | Medium | NFR-SC-05 "record every creation, change and deletion of operational records" | The design audits 27 operational tables, not every table. | Name the audited record classes instead of "every". |
| M11 | Medium | FR-HZ-01 "flood, fire, gas-leak and structural-collapse hazards"; FR-FC-07 "trapped, injured or hazard"; FR-MR-06 road conditions | The design has more values: hazards also SMOKE, DOWNED_POWER_LINE, DEBRIS, SINKHOLE, CHEMICAL_SPILL; citizen requests also MEDICAL, FIRE, MISSING_PERSON, OTHER; roads also DAMAGED and UNKNOWN. | Write "at least" or list all values. |
| M12 | Medium | Table 3-38 "O1 → OBJ-01, OBJ-04" and its intro sentence | O1 to O7 are not defined in Chapter 1, the intro sentence is garbled, and the OBJ-06 row has no code. | Map requirements directly to OBJ-01 to OBJ-06 and rewrite the sentence (agree with Yassin). |
| M13 | Medium | Section 3.2.4 | No requirement sets AI quality targets (detection recall, damage-grade accuracy), although Chapter 1 says models must be evaluated on held-out data. | An NFR with metric names and "to be agreed" targets. |
| M14 | Medium | FR-PD-06 "a configured limit"; FR-PT-05 "a configured interval"; FR-FC-02; FR-HZ-05 "configured rule distance"; FR-HZ-09 "inside or near"; IR-UI-06 "freshness limit"; NFR-PV-04 "agreed retention period" | Untestable as written. Section 3.3 uses 30 m as an example rule distance and 5 minutes for stale positions. | A proposed default for each, marked "to be confirmed". |
| M15 | Medium | FR-PD-01 "different altitudes and camera angles"; FR-PD-02 "only partly visible"; FR-MR-03 | No measurable condition. | An altitude range or test set, or a link to the AI evaluation requirement (M13). |
| M16 | Medium | Table 3-4 says conventions apply to "every requirement table" | IR and NFR tables have no Actor column. FR-MR-08 actor is "Analyst" but UC-04's actor is "Analyst or Commander". FR-HZ-02 and FR-HZ-03 actor "Analyst" is not in the Analyst row of Table 3-5. | Say IR and NFR apply to the System; align Table 3-5 with the actors used. |
| M17 | Medium | Use case diagram, Section 3.3.7 | The 3.3 diagram shows "UC-09 includes UC-04", "UC-06 includes UC-04", "UC-05 includes UC-02", an SOS use case (FR-FC-03) and Platform Administrator use cases. Section 3.2 names these links only as alternatives and has no SOS use case. | Agree with Ali (see [person5_ali.md](person5_ali.md)): add the include notes and an SOS use case to 3.2, or Ali simplifies the diagram. |
| M18 | Low | IR-SW-01 "storage key and content checksum"; IR-CM-02 "persistent connection"; NFR-SC-01 "adaptive hashing algorithm"; NFR-DQ-04 "WGS 84 ellipsoid"; F2 text "Dijkstra or A*"; F6 text "DINOv2" | Section 3.2 says requirements "describe behaviour, not construction". These are design choices, and Section 3.3 already covers them (D-03, D-09, D-10). | Keep the outcome only, for example "shall not store passwords in readable form". |
| M19 | Low | Table 3-3 F1 "A damage grade for every building"; "a reviewer can always answer" | Written as delivered and absolute. | "each assessed building"; "is intended to". |
| M20 | Low | Table 3-4 "Numbers in Section 3.2.4 are proposed targets" | Numbers also appear outside 3.2.4 (IR-UI-01 1366 × 768, IR-CM-01 TLS 1.2, FR-MR-10). | "Numbers in this section". |
| M21 | Low | NFR-RL-02 "No upload ... shall be lost"; NFR-PF-06 "at least 200 concurrent users" | No test condition or workload. | Add the condition. |
| M22 | Low | Intro "It follows SRS headings 3.1 to 3.4 of the Project I guide [4]"; Tables 3-4 and 3-5 say "this chapter" | In the merged report these are 3.2.1 to 3.2.4, inside a section. "Requirement Conventions" and "Actors" headings are unnumbered. | "SRS headings 3.1 to 3.4 appear here as 3.2.1 to 3.2.4"; "section" for "chapter"; style both headings consistently. |

## Appendix C (SWOT)

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| S1 | Medium | "Floods and earthquakes in the region keep the need visible."; "Civil-defence and emergency services increasingly use drones" | No citation. | Cite a source or soften. |
| S2 | Medium | "the intended open-source geospatial stack keeps licence costs low for public agencies" | No source. | Cite or remove. |
| S3 | Medium | "Public aerial disaster datasets exist [2], [15]" | [2] xBD is satellite imagery and [15] VisDrone is a general drone benchmark, not a disaster dataset. | Correct the wording (Bela agrees, see L10). |
| S4 | Medium | Table C-1 "Minimal citizen data, no face recognition" citing NFR-PV-01 to NFR-PV-04 | No requirement says "no face recognition". | Add the requirement or remove the phrase. |
| S5 | Low | "Every AI result keeps a link to the model version ... so a commander can check"; "Routing takes into account ..." | Present tense as if working. | "is specified to". |

## Missing content to add

- A verification method and acceptance target per requirement (M2).
- Requirements for invitation and assignment responses, case confirmation, report pending approval and return to draft, unmatched citizen requests, and AI quality targets (M3, M4, M7, M8, M13).
- Proposed default values for every configured parameter (M14).

## Your review duty

You review Ali's Section 3.3. The joint items are in [person5_ali.md](person5_ali.md).
