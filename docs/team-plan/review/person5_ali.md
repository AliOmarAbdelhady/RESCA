# Person 5, Ali: Section 3.3 System Design

See the [review index](README.md). Section 3.3 is complete in the report (51 pages, Figures 3-2 to 3-34, Tables 3-39 to 3-48, references [27] to [31]). Its sources and builder are in `docs/documentation/chapter5/`.

## Fixed with this review

The review of Section 3.2 found three citation problems in Section 3.3. They are fixed in `section_3_3.md`, and the report was rebuilt with `build_section.py`.

| Problem | Fix |
|---|---|
| Decision D-02 (modular application with background workers) cited NFR-MT-01 to NFR-MT-03, which cover rules as data, model versions and position volume, not modularity. | Now cites NFR-MT-02, NFR-RL-04 and NFR-PF-06. |
| "Draft reports remain visible only inside the authoring agency" cited FR-RP-06 alone, which covers sharing a published report. | Now cites FR-RP-04 and FR-RP-06. |
| Twelve requirements were never cited in Section 3.3: IR-HW-03, IR-HW-04, IR-CM-05, NFR-PF-01, NFR-PF-03, NFR-PF-06, NFR-RL-01, NFR-RL-02, NFR-SF-04, NFR-DQ-02, NFR-DQ-05, NFR-MT-04. | Each is now linked in Table 3-48 to the design element that serves it. |

## Joint items with Mahmoud (Section 3.2)

Section 3.3 follows the approved database design. Where Section 3.2 differs, the better fix is in 3.2, but both owners should agree.

| Item | Section 3.3 and the database | Section 3.2 | Proposed resolution |
|---|---|---|---|
| Case confirmation | A case from a track starts DETECTED and must be confirmed before assignment. | UC-06 assigns without confirmation. | 3.2 adds the step (M3). |
| Report states | DRAFT, PENDING_APPROVAL, APPROVED, PUBLISHED, and back to DRAFT on request. | FR-RP-04 lists draft, approved, published. | 3.2 adds the state (M4). |
| Closed case states | TRANSPORTED, DECEASED, FALSE_ALARM. | UC-06 closes the case at "rescued". | 3.2 aligns (M5). |
| Audit scope | 27 of 56 tables are audited. | NFR-SC-05 says "every" record. | 3.2 rewords (M10). |
| Use case diagram (Figure 3-31) | Shows include links, an SOS use case and Platform Administrator use cases. | Not present as use cases. | Decide together. If 3.2 does not add them, Ali removes them from Figure 3-31. |

## Still open for Ali

- Figures 3-16 to 3-22 are empty, captioned slots for design illustrations. The team decides whether they are filled before submission.
- The data dictionary for the appendices is in `docs/documentation/chapter5/appendix_data_dictionary.md`; Mesbah decides where it goes.
- The figure numbers assume Joe adds exactly one figure (3-1). If that changes, update the numbers in `section_3_3.md` and rebuild.
- Mahmoud reviews this section.
