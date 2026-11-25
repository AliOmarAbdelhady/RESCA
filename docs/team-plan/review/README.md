# Report Review, 23 November 2026

This folder records a full review of the merged report, `docs/documentation/main/Project 1 Docs.docx`, at `main` commit `807715c` plus the Section 3.3 citation fixes made with this review. Each chapter was checked against three sources:

- the team work plan, [`documentation-work-plan.md`](../documentation-work-plan.md), which sets each person's scope and the report rules;
- the approved platform design, [`2026-11-23-resca-database-erd-design.md`](../../superpowers/specs/2026-11-23-resca-database-erd-design.md), and the implemented schema in `database/`;
- Section 3.3 System Design, [`section_3_3.md`](../../documentation/chapter5/section_3_3.md), and Section 3.2 Requirements, which the other chapters must not contradict.

Every finding quotes the report text it refers to. Nothing here changes anyone's section; each owner decides how to fix their part.

## Files

| File | Owner | Scope |
|---|---|---|
| [person1_yassin.md](person1_yassin.md) | Person 1, Yassin | Chapter 1; Chapter 5 with Mesbah |
| [person2_bela.md](person2_bela.md) | Person 2, Bela | Chapter 2, reference list, Appendix D |
| [person3_joe.md](person3_joe.md) | Person 3, Joe | Section 3.1 System Description |
| [person4_mahmoud.md](person4_mahmoud.md) | Person 4, Mahmoud | Section 3.2 Requirements, Appendix C |
| [person5_ali.md](person5_ali.md) | Person 5, Ali | Section 3.3 System Design (fixes made, joint items) |
| [person6_mesbah.md](person6_mesbah.md) | Person 6, Mesbah | Front matter, Chapter 4, Chapter 5, appendices, assembly |

## State of the report

| Part | Owner | State |
|---|---|---|
| Front matter | Mesbah | Present. Abstract empty; cover and declaration details unconfirmed; lists and contents out of date. |
| Chapter 1 | Yassin | Full draft. Vocabulary and scope do not yet match the approved design. |
| Chapter 2 | Bela | Draft of about 1,300 words. No related-systems comparison; two of the five features not covered. |
| Section 3.1 | Joe | Not started. Every subsection is a placeholder. |
| Section 3.2 | Mahmoud | Full draft, 161 unique requirement IDs, Tables 3-3 to 3-38. Needs verification methods and a few missing requirements. |
| Section 3.3 | Ali | Complete, 51 pages, Figures 3-2 to 3-34, Tables 3-39 to 3-48. |
| Chapter 4 | Mesbah | Draft. Honest about limits; a few overstated requirement links. |
| Chapter 5 | Yassin and Mesbah | Headings only. |
| References | Bela | [1] to [31] in first-citation order; several entries incomplete. |
| Appendices | Mesbah and Bela | A empty; B stale; C and D need citations. |

## Checks that passed

- `main` holds every pushed branch; no work was removed or overwritten by the merges.
- All 161 requirement IDs in Section 3.2 are unique, and every ID cited in Sections 3.3, Chapter 4 and Appendix C exists in 3.2.
- UC-01 to UC-10 have the same titles in Sections 3.2 and 3.3.
- Agency names and role names in Section 3.2 match the approved design.
- Every citation [n] in the body exists in the reference list, and the list follows first-citation order.
- Section 3.3 names no AI model, so it does not conflict with Chapters 2 and 4 on model names.

## Shared vocabulary (use exactly these words)

| Item | Approved wording |
|---|---|
| Agencies | Government, Police, Emergency Medical Services (EMS), Fire |
| User roles | Platform Administrator, Agency Administrator, Commander, Analyst, Field Responder; Citizen through the citizen channel |
| Not a user role | Hospital coordinator (a stakeholder; hospitals are receiving facilities) |
| Incident model | One shared incident; a lead agency invites other agencies; each agency runs its own missions, assigned to teams or individuals |
| Features | F1 Before/After Damage Assessment and Restoration Cost; F2 2D/3D Mapping and Rescue Route Planning; F3 Aerial Person Detection under Partial Visibility; F4 Multi-Object Person Tracking and Assistance Cases; F5 Compound Hazard Alerts ("Electrified Water"); F6 General Reports |
| Database | PostgreSQL 18 with PostGIS 3.6, pgRouting and pgvector; row-level security; WGS 84 coordinates, distances in metres |
| Tense | Proposed behaviour is written as "is designed to", "shall" or "is proposed"; never as achieved |
| Captions | "Table 3-3: Title" and "Figure 3-2: Title" (colon) in every chapter |

## What blocks the report, in order

1. Section 3.1 (Joe): write it first. Section 3.2 and Section 3.3 both point to it, and Figure 3-1 and Tables 3-1 and 3-2 are reserved there.
2. Chapter 1 vocabulary and scope (Yassin), so every later chapter uses the same terms.
3. Section 3.2 verification methods and the missing requirements (Mahmoud).
4. Chapter 2 related systems and research gap (Bela).
5. Chapter 5 and the abstract (Yassin and Mesbah), after 1 to 4.
6. Final assembly (Mesbah): refresh contents and lists, captions, acronyms, cover details, remove the editorial tracker.

## Decisions needed from the supervisor

- Abstract length (150 to 200 or 200 to 250 words) and whether a page minimum applies.
- Whether Section 3.3 at 51 pages is acceptable, or the nine ERD pages should move to an appendix next to the data dictionary.
- Expected depth of the prototype chapter.
- Formal citation for the course guide [4] and the report guidelines [5].
