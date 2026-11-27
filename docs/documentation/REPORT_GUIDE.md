# RescueVision graduation report guide

How the team works on the Project I report. Paths in backticks are from the repository root. For building the application, read the root [AGENTS.md](../../AGENTS.md).

## Current focus

Work on the Project I graduation report. Keep changes to report material, evidence, and editorial coordination. Change application code or run new experiments only if the user explicitly changes the scope.

Use the [team documentation plan](../team-plan/documentation-work-plan.md) for assignments and [Mesbah's Person 6 plan](../team-plan/person6_plan.md) for the detailed outline and formatting checklist. Use the university requirements guide and Word template when available.

## Local report workspace

- Put the Skeleton Word export in [`docs/documentation/skeleton/`](skeleton/) and the Main Word export in [`docs/documentation/main/`](main/). Keep the original filenames so the two versions can be compared.
- Keep the university template and requirements guide in `.local-report/source/` and use `.local-report/working/` for edits. Confirm the team's master before working from it.
- For layout, preserve the university template specified in the team plan. For citations, use IEEE bracketed numbers in first-citation order and reuse the same number for each source. Confirm with the supervisor if an IEEE publication template is also expected.
- New Word exports and local drafts are Git-ignored by default. The two original snapshots under `docs/documentation/` were explicitly selected for Git. Merge local edits into the shared report after checking the latest team copy.

### Report versions

- [Skeleton](<skeleton/Project 1 Docs — Skeleton (Marwan draft).docx>) is the five-chapter outline with author prompts and figure placeholders. Its Chapter 2 points to Bela's merged draft in Main. The original Skeleton snapshot is in commit `dac7162`.
- [Main](<main/Project 1 Docs.docx>) is the complete working draft: front matter and abstract, Chapters 1 to 5, the references and Appendices A to D. On 27 November 2026 the fixes from the [team review](../team-plan/review/README.md) were applied across it (see "Review fixes" below); each owner still confirms the changes to their part.
- Use the same margins as page 1 throughout the working report, including equal 2.54 cm left and right margins. Keep the declaration signatures in one two-column table.
- Each DOCX has an editable `.source/` folder beside it. Edit `package/word/document.xml` for content or `package/word/styles.xml` for styles, then run `python3 docs/documentation/build_docx.py build "<path to DOCX>"`. After editing directly in Word, run the same command with `extract` to refresh the corresponding source package.
- Some parts of Main are written in Markdown and built into it: the abstract, Chapter 2, Section 3.1, Chapter 5 and Appendices A, B and D in [`sources/`](sources/), and Section 3.3 in [`chapter5/section_3_3.md`](chapter5/section_3_3.md). Edit the Markdown, then run `python3 docs/documentation/tools/build_report.py` (Section 3.3: `chapter5/tools/build_section.py`, which calls it). Do not edit those parts in Word, or the next build overwrites the change.
- Cite sources as `[@key]` in Markdown, with the entry in [`sources/references.md`](sources/references.md). `build_report.py` numbers every citation in the report in first-citation order, including the numbers typed in Word, and rebuilds the reference list; each entry keeps a `ref_<key>` bookmark. Add a new source to `references.md`, not to the list in Word.
- Chapter 4 has six evidence figures, two tables, the Maxar Open Data citation, and links to the requirement IDs of Section 3.2. Word refreshes the contents and caption lists when the file is opened (`updateFields`); check them before exporting the submission PDF.
- Keep empty bordered boxes above the captions for pending screenshots and diagrams. Replace the corresponding box paragraph when the actual visual is ready.

## Team and report ownership

Team roster: Mesbah, Mahmoud, Ali, Bela, Yassin, and Youssef. Mesbah confirmed Yassin as Person 1, Bela as Person 2, Mahmoud as Person 4, Ali as Person 5, and himself as Person 6. Joe is Person 3. Person numbers identify writing assignments. Chapter numbers follow the university report outline.

| Person | Confirmed owner | Report responsibility | Reviewed by |
| --- | --- | --- | --- |
| 1 | Yassin | Chapter 1 introduction, objectives, scope, glossary, and constraints. Co-writes Chapter 5 with Mesbah. | Ali |
| 2 | Bela | Chapter 2 Literature Review and Background, including related systems, the research gap, and references. Coordinates appendices and citations with Mesbah. | Mesbah |
| 3 | Joe | Section 3.1 System Description, including workflow, user roles, assumptions, and limitations. | Yassin |
| 4 | Mahmoud | Section 3.2 User and System Requirements, including functional and quality requirements, interfaces, written use cases, and traceability. | Person 3 |
| 5 | Ali | Section 3.3 System Design, including diagrams, design rationale, and screen illustrations. | Mahmoud |
| 6 | Mesbah (Marwan Mesbah) | Chapter 4 System Prototype, front matter, Chapter 5 with Person 1, and final report assembly and review. | Person 2 |

### Contributions and evidence

| Teammate | Contribution or current evidence |
| --- | --- |
| Mesbah | Authored the mapping prototype and research notes (`f0b600f`), then the Person 6 plan and six prototype figures (`03b3fb0`). Git records his name as `Marwan` and `Marwan Mesbah`. |
| Ali | Section 3.3 System Design is in progress, as confirmed by Mesbah. Ali authored the documentation work plan (`22bc575`) and the database and ERD materials (`6815a05`, `3640e18`). Section 3.3 is now in Main: 26 figures, Tables 3-39 to 3-48, references [27] to [31], and empty slots for screen illustrations (Figures 3-16 to 3-22). Sources and the builder are in `docs/documentation/chapter5/`; the team review with requests per person is in [`docs/team-plan/review/`](../team-plan/review/README.md); the plan is [`person5_plan.md`](../team-plan/person5_plan.md). A generated data dictionary for the appendices is in `docs/documentation/chapter5/appendix_data_dictionary.md`. Git records his name as `AliOmarAbdelhady`. |
| Mahmoud | Authored the 23 November 2026 requirements draft, `RescueVision_Person4_Requirements_SRS_Section3.pdf`, as confirmed by Mesbah. The PDF is stored locally for reference. |
| Bela | Authored the [ranked paper list](../research_papers.md) and [Tier 1 summaries](../tier1_papers_summary.md) as `Mohamed Belal` (`c327c26`, `b7c0b68`). Rewrote Chapter 2 on 27 November 2026 (related systems, use context, cited research gap, cost, detector and compound-hazard themes), consolidated the references into [`sources/references.md`](sources/references.md), added the search log to Appendix D, and applied the team review fixes across the report. The classifier configuration uses DINOv2; Chapter 2 describes DINOv3 as an evaluation candidate. |
| Yassin | Owns Chapter 1. Main has a full draft with the objectives, scope, glossary, and constraints. Yassin and Ali should confirm its wording and review status. Yassin co-writes Chapter 5 with Mesbah. |
| Youssef | No commits attributable to this name in the visible history. |
| Joe | Person 3, owner of Section 3.1 System Description. Bela drafted the section on 27 November 2026 from the approved design and [`person3_joe.md`](../team-plan/review/person3_joe.md) ([`sources/section_3_1.md`](sources/section_3_1.md), Figure 3-1 and Tables 3-1 and 3-2); Joe to review and take ownership. |

History checked through `origin/main` at `22bc575` and `origin/feature/mapping-routing` at `03b3fb0`. Use Git authorship to credit specific contributions and confirm chapter ownership with the team. Add shared-document contributions when their author and section are confirmed.

## Person 6 progress

The repository has the plan, prototype evidence, and a complete editable Main draft in which every chapter has content. Owner confirmation, the open items below and the submission PDF remain pending.

- [x] Commit the 2D satellite mapping prototype (`f0b600f`).
- [x] Commit the Person 6 plan and six [prototype figures](../team-plan/figures/) (`03b3fb0`).

### Start now

- [x] Merge the Word reports into one editable Main draft with heading styles and contents and figure/table fields.
- [x] Compile the abbreviations list from the current Main draft.
- [ ] Check the editable draft against the university requirements guide and review first-use acronym definitions after the remaining chapters arrive.
- [x] Draft the System Prototype chapter using the existing figures, captions, imagery credits, and an evidence coverage table.
- [x] Link Chapter 4's dated imagery, 2D map, and comparison evidence to the relevant IDs in Person 4's 23 November 2026 SRS draft.
- [ ] Confirm Chapter 4 scope and terminology with Persons 1 and 3, verify the IDs against Person 4's approved version, and have Person 2 check the evidence claims and citations.
- [x] Merge Mahmoud's requirements into Main as Section 3.2. Keep the original requirement and use-case IDs, map the working goals to the Chapter 1 objectives, and place the SWOT analysis in Appendix C.
- [x] Merge Bela's literature review into Chapter 2, verify the cited core studies against the original sources, and consolidate references in first-citation order.
- [ ] Review Chapter 2 with Bela. Chapter 2 now has a related-systems comparison and a use context; a market assessment of adopters and prices was not done and is stated as outside the evidence.
- [ ] Review the provisional nonfunctional targets, hazard rule distances, proposed defaults marked “to be confirmed” in Section 3.2, and bilingual interface scope with the team and supervisor. Section 3.1.3 uses the role wording of Table 3-5.
- [x] Draft the acknowledgments and add the contribution record to Appendix B. The editorial tracker was removed from Main on 27 November 2026; its open items are in "Open items" below.
- [ ] Confirm the department, formal degree title, submission month and year, name spelling and author order. Collect signatures and dates. Decide whether to include the optional dedication.
- [ ] Confirm the supervisor's decisions on chapter order, expected prototype depth, abstract length, page minimum, and submission files.

### As chapter drafts arrive

- [ ] Collect reviewed chapters and figures, merge them into the master, and make terminology, tense, headings, captions, and numbering consistent.
- [ ] Get objectives and scope from Person 1, features and limitations from Person 3, requirement IDs from Person 4, and design figures and captions from Person 5.
- [ ] Review Person 2's literature chapter for clarity, structure, and formatting. Have Person 2 review the prototype and closing sections for claims and citations. Coordinate reference order and appendices with Person 2.
- [ ] Write Chapter 5 with Yassin once the objectives and Chapter 3 drafts are agreed. Draft the roughly 200-word abstract after that and confirm the final length with the supervisor. Both were drafted on 27 November 2026 ([`sources/chapter5.md`](sources/chapter5.md), [`sources/abstract.md`](sources/abstract.md)); Yassin and Mesbah to review.

### Review fixes, 27 November 2026

Every item in [`docs/team-plan/review/`](../team-plan/review/README.md) was addressed in Main except those listed under "Open items". Owners confirm the changes to their part before submission.

- [x] Chapter 2, references and Appendix D (L1 to L11, R1 to R8, D1, D2): rewritten in `sources/`; 72 references in one IEEE style with access dates; search log in Table D-2.
- [x] Section 3.1 drafted (Figure 3-1, Tables 3-1 and 3-2), so the numbering of Sections 3.2 and 3.3 is unchanged.
- [x] Chapter 1 (C1 to C15): four agencies, role-based audience, F1 to F6 scope rows, revised OBJ-02 to OBJ-04, success criteria linked to requirement and use-case IDs, glossary terms, acronyms at first use, Section 1.8.
- [x] Section 3.2 and Appendix C (M1 to M22, S1 to S5): verification rule in Table 3-4, six new requirements (FR-AC-10, FR-AC-11, FR-RP-11, FR-FC-12, FR-FC-13, NFR-DQ-06; 167 in total), case verification and report states aligned with Section 3.3, proposed defaults, Table 3-38 mapped to OBJ-01 to OBJ-06.
- [x] Chapter 4 (P1 to P14): requirement-draft notes removed, scene IDs and licence in Table 4-1, Table 4-2 marks uncovered objectives, captions say screenshot or output.
- [x] Front matter (F1, F9, F11 to F13): abstract, descriptive subtitle, acknowledgment, acronym list rebuilt, one caption style. Appendix A has the full ERD (Figure A-1) and the data dictionary; Appendix B is current.
- [x] RESCA replaced by RescueVision in both DOCX files (the sources already used the name).

### Open items

- [ ] Cover and declaration (F5 to F8, F10): department, degree title, submission month and year, the official spelling of Youssef’s name (cover and declaration differ), author order, and whether each student signs a separate declaration.
- [ ] Course documents [4] and [5] (R2): real titles, issuing department and year, agreed with the supervisor.
- [ ] Chapter 4 (P2, P9): the script that produced the change mask is not in the repository, so the chapter says its method is undocumented; Mesbah to add it or confirm. Confirm Maxar’s required credit line.
- [ ] Section 3.3 (Ali): Figures 3-16 to 3-22 are still empty design-illustration boxes.
- [ ] Owners confirm the changes to their sections, and the supervisor decisions in the review index are recorded.

### Before submission

- [ ] Open Main in Word and accept the field update, then check the contents, figure/table lists, cross-references and abbreviations. Citations are numbered in first-citation order by `build_report.py`.
- [ ] Export the PDF, inspect every page, resolve review comments, and get all six authors' approval. Hand over the editable master and the final PDF.

## Prototype evidence

Start with the [mapping prototype](../../mapping/README.md) and the committed figures. The current evidence covers 2D satellite imagery, before/after comparison, and imagery preparation. The change overlay shows pixel differences and the displayed routes are placeholders. Describe 3D views, person tracking, hazard markers, and operational route guidance as proposed capabilities unless the team supplies verified evidence. Label design illustrations as proposals and credit the source of satellite imagery.

## Keeping this file current

When report work changes an item's status, update this checklist in the same change. Mark an item complete after checking the deliverable or receiving confirmation, and add a link or commit when available. If work lives in a shared document, record its link and review status once confirmed. Record blockers beside the affected item. Fill in the ownership table as the team confirms person numbers.
