# Person 2, Bela: Chapter 2, References and Appendix D

See the [review index](README.md) for the shared vocabulary. Severity: High blocks other chapters or misses required content; Medium affects consistency; Low is polish.

## Chapter 2 problems

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| L1 | High | "RELATED SYSTEMS AND MARKET POTENTIAL": "Table 2-1 compares the uses and scope of these resources." | The work plan asks for a related-systems table (purpose, intended users, capabilities, documented limitations, source). Table 2-1 compares three imagery datasets (Maxar, xBD, FloodNet), not systems. No operational disaster-response platform is compared. | A real related-systems table built only from sources you have verified. Write "not established by the source" where a detail is unknown. |
| L2 | High | "A market assessment would require separate evidence on operational tools, intended adopters, and deployment conditions." | The heading promises market potential, but the section declines to give any. | A short, cited use and market context, or rename the heading after the supervisor agrees it is not needed. |
| L3 | High | "RESEARCH GAP: ... How can a shared map distinguish source imagery, model-generated observations, and verified incident records" | The gap is a question with no citation showing that existing systems lack this. | A gap paragraph tied to the related-systems table, with citations, covering what existing work does not do: one shared multi-agency incident, provenance of AI results, human-verified assistance cases, compound hazards. |
| L4 | High | Coverage of features | F1 restoration cost and F5 Compound Hazard Alerts ("Electrified Water") are two of the approved features and are not discussed. Hazus [23] is in the reference list but not used in Chapter 2. | Add a theme on damage cost estimation and a theme on compound or cascading hazards. |
| L5 | High | "The ranked list identifies detector families for literature comparison." | F3 person detection cites only VisDrone [15], the SARD study [16] and ByteTrack [17]. No detector is compared, although Appendix D ranks several. | A short comparison of detector families with citations, ending in what it means for RESCA. |
| L6 | High | Heading "FUTURE WORK" in Chapter 2 | Empty heading. Chapter 5 already covers future work. | Delete it or write it. |
| L7 | Medium | Length about 1,300 words; "Hazards and movement" and "Coordination" themes are 3 to 4 sentences | The work plan asks, for each important source, its purpose, approach, findings, limits and relevance, and a closing note per theme. | Expand the thin themes. Add one or two reported figures per core study from `docs/tier1_papers_summary.md`, with the source. |
| L8 | Medium | "It started from Bela's ranked list"; Appendix D "Bela's research inventory" | A first name in formal body text. | "the team's ranked list" or a reference to Appendix D. |
| L9 | Medium | "The repository uses EfficientNet-B3 ... The repository has SegFormer configurations"; "The current classifier configuration freezes a DINOv2 backbone [13]." | "Repository" is not explained, and readers may read "configured" as "trained". The experiments in `docs/experiments.md` are still pending. The backbone is DINOv2 here and DINOv3 as a candidate. | Say "the project configuration", add that no trained results exist yet, and confirm one backbone name with the ML owner for all chapters. |
| L10 | Medium | "Existing aerial research in the report provides more direct application context." | Vague. VisDrone [15] is a general drone benchmark, not a disaster dataset, but Appendix C calls it one. | Reword; tell Mahmoud to correct Appendix C. |
| L11 | Low | Table 2-2 | ChangeFormer and Siamese change detection appear in `docs/research_papers.md` as used, but no paper is cited. | Cite the change-detection source or drop the claim. |

## Reference list problems

| # | Severity | Entry | Problem | What we need |
|---|---|---|---|---|
| R1 | High | [1] to [3] "(accessed 22 November 2026)", [21] "Accessed: Nov. 23, 2026", and [9], [10], [11], [19], [25], [26], [27], [29], [30] with no date | Some online sources lack access dates, and two date styles are used. | An access date for every online source, in one IEEE style. |
| R2 | High | [4] "supplied course guide, 3 pages, undated"; [5] "Project 1 Docs.pdf, 25 pages, undated" | No issuing body or year; [5] is cited by its file name. | The real title, issuing department and year, agreed with the supervisor. |
| R3 | Medium | [13] DINOv2 has no volume, DOI or URL; [15] to [18] have no DOI or URL; [20] and [23] have no URL, and [23] has no year | Incomplete entries cannot be verified. | Complete each entry. |
| R4 | Medium | [1] and [3] ("web resource") | Not in IEEE format. | One IEEE style for all entries. |
| R5 | Medium | [1] to [3] straight quotes; others curly. Mixed "[Online]. Available:" and "Available:" | Inconsistent typography. | Normalise. |
| R6 | Medium | Appendix D rows 8 to 28, for example "Focal Loss for Dense Object Detection (RetinaNet, 2017)" | 21 of the 28 papers have no reference entry, so a reader cannot verify them. | Add entries for the papers you keep, or label the table "candidate reading, not cited". |
| R7 | Low | [6] to [11] | Mixed use of page numbers and "et al." | IEEE lists up to six authors, then "et al." |
| R8 | Low | References [27] to [31] (added by Section 3.3) | New entries: UML 2.5.1, ISO/IEC/IEEE 42010:2022, PostgreSQL row security, PostGIS manual, Dijkstra 1959. | Check them against your style; [28] is a standard and follows the IEEE standard format. |

## Appendix D problems

| # | Severity | Where | Problem | What we need |
|---|---|---|---|---|
| D1 | Low | Row 13 "Gal &amp; Ghahramani" | An HTML entity is visible. | "Gal & Ghahramani". |
| D2 | Low | Row 16 "The optimiser used to train the models"; row 11 "which the training relies on" | Written as if the models are trained. | "planned" or "candidate". |

## Missing content to add

- A related-systems table and a cited research gap.
- Themes on restoration cost (F1), compound hazards (F5) and person detectors (F3).
- A search log (search terms, date, reason for inclusion), as the work plan requires.
- Complete references and a decision on the uncited rows of Appendix D.

## Your review duty

You review Mesbah's Chapter 4 and the closing chapter for claims and citations, and you coordinate reference order with every author.
