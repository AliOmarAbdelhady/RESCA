# Person 1, Yassin: Chapter 1 and Chapter 5

See the [review index](README.md) for the shared vocabulary. Severity: High blocks other chapters or contradicts the design; Medium affects consistency; Low is polish.

## Chapter 1 problems

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| C1 | High | Intro: "authorized emergency-service agencies, including police, ambulance, and fire services" | Leaves out Government, the fourth agency in the design and Section 3.2. Uses "ambulance" where 3.2, 3.3 and the acronym list use EMS. | Name the four agencies: Government, Police, Emergency Medical Services (EMS), Fire. Define EMS at first use. |
| C2 | High | Table 1-3 "Included capabilities and boundaries" | No row for F5 Compound Hazard Alerts ("Electrified Water"), restoration cost (F1), the citizen channel, or the shared multi-agency incident. "Hazard information" only says "Display recorded hazards". The six features of Table 3-3 are never named. | Add scope rows for these, using the feature names of Table 3-3. |
| C3 | High | Table 1-1: "Incident coordinators", "Police and ambulance representatives", "Hospital coordinators (stakeholders)" | Audience terms do not match the roles in Table 3-5. "Incident coordinator" is not a role. Government and Fire are missing. | Use Commander, Analyst and Field Responder; add Government and Fire; mark hospital coordinators clearly as stakeholders who are not platform users. |
| C4 | High | Table 1-5 Project glossary | Missing terms that later chapters depend on: Agency, Lead agency, Shared incident, Mission, Team, Commander, Analyst, Field Responder, Citizen, Compound hazard, Electrified Water, Restoration cost, START triage, Orthomosaic. Glossary says "Responder" where 3.2 says "Field Responder". | Add the terms and align "Responder". |
| C5 | Medium | Table 1-2 OBJ-01 to OBJ-06 and Section 3.2 Table 3-38 ("O1 → OBJ-01, OBJ-04") | No objective covers hazard alerts, cost estimation or reports. Table 3-38 maps seven goals O1 to O7 that Chapter 1 never defines. | Agree with Mahmoud: either extend the objectives or have 3.2 map straight to OBJ-01 to OBJ-06. |
| C6 | Medium | 1.4.5 "SC-01 ... SC-07" and Table 1-7 "Traceability convention" | The success criteria are not linked to any requirement or use case, so the traceability Table 1-7 promises is missing. | Give each SC the FR or UC IDs it depends on (ask Mahmoud), or remove the promise. |
| C7 | Medium | 1.4.5: "Numerical acceptance thresholds and latency targets must be set before final acceptance testing" | Section 3.2.4 already proposes numeric targets. | Refer to Section 3.2.4. |
| C8 | Medium | 1.4.2: "Detailed technology choices ... are addressed in later sections" | Section 3.1.5 Intended Technologies is still empty. | Keep, and check again after Joe delivers 3.1.5. |
| C9 | Medium | Glossary "SDD: Software Design Document" vs acronym list "SDD: Software Design Description" | Two expansions of one acronym. | Use "Software Design Description" (the IEEE term). |
| C10 | Medium | Intro "OCHA describes data responsibility"; Table 1-8 "GPU access"; "RGB" | Acronyms used before they are defined. | Expand OCHA, GPU and RGB at first use. |
| C11 | Medium | 1.1: "The purpose of this Software Requirements Specification (SRS) introduction" and "evaluation sections" | The report is a full requirements and design report, and it has no evaluation chapter. | Say "this report"; replace "evaluation sections" with the real chapters. |
| C12 | Medium | Headings "Background and Motivation" and "Report Organization" are unnumbered; 1.1 to 1.7 are numbered | Mixed numbering and capitalisation. | One heading scheme using the template styles. |
| C13 | Medium | Report Organization: "Chapter 5 discusses the work ... and identifies future work." | Does not mention Sections 3.1 to 3.3, the references or Appendices A to D. | Describe the real structure. |
| C14 | Low | "Table 1-1 Intended audience"; Table 1-4 cell "SC-01 OBJ-01" | Caption has no colon; two IDs in one cell. | "Table 1-1: Intended audience"; put the objective in its own column. |
| C15 | Low | Heading "Measurable Success Criteria" | The criteria are pass conditions without numbers. | Consider "Proposed Success Criteria". |
| C16 | Low | Chapter 1 hand-over | The work plan asks for a short list of assumptions needing confirmation. | Send the list to Mesbah for the open-items tracker. |

Chapter 1 is well hedged: it uses "proposed" consistently and makes no claim of achieved results.

## Chapter 5 (with Mesbah)

The chapter has only the headings DISCUSSION, LIMITATIONS and CONCLUSION. The title promises Future Work, which has no heading. Chapter 4 already refers to Chapter 5 for Project II work.

| Part | Content | Inputs |
|---|---|---|
| Discussion | One paragraph per objective, OBJ-01 to OBJ-06, linking requirements (Table 3-38), design (Section 3.3, Table 3-48) and prototype evidence (Table 4-2). How the proposal answers the research gap. | Chapter 1 objectives; Mahmoud's mapping; Section 3.3; Bela's gap statement |
| Limitations | Data quality and local accuracy, human review of every AI result, privacy of person data, unknown power state treated as energised, no trained-model results yet, single-area prototype. | Table 1-8; Appendix C; Chapter 4 limitations; `docs/limitations_and_ethics.md` |
| Conclusion | The problem, what Project I delivered (requirements, design, preliminary prototype), and what the evidence does and does not show. No unmeasured claims. | All chapters stable |
| Future Work (add heading) | Project II: train and evaluate the planned models, route computation on the road graph, 3D view, person tracking, compound hazard rules, field application, user testing. | `docs/experiments.md`; Chapter 4 "next prototype steps" |

## Your review duty

You review Joe's Section 3.1 once it is written. Check its role and feature names against Tables 3-3 and 3-5.
