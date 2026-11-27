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
- [Main](<main/Project 1 Docs.docx>) is the merged working draft. It contains the authored Chapter 1, Bela's Chapter 2 literature review, Mahmoud's requirements in Section 3.2, Mesbah's Chapter 4 prototype draft, and supporting material in Appendices C and D.
- Use the same margins as page 1 throughout the working report, including equal 2.54 cm left and right margins. Keep the declaration signatures in one two-column table.
- Each DOCX has an editable `.source/` folder beside it. Edit `package/word/document.xml` for content or `package/word/styles.xml` for styles, then run `python3 docs/documentation/build_docx.py build "<path to DOCX>"`. After editing directly in Word, run the same command with `extract` to refresh the corresponding source package.
- Chapter 4 has six evidence figures, two tables, the Maxar Open Data citation, and links to Mahmoud's draft requirement IDs. Refresh the contents and caption lists in Word after editing and before exporting the submission PDF.
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
| Bela | Authored the [ranked paper list](../research_papers.md) and [Tier 1 summaries](../tier1_papers_summary.md) as `Mohamed Belal` (`c327c26`, `b7c0b68`). Main integrates the seven core studies into Chapter 2 and records all 28 ranked papers in Appendix D. The classifier configuration uses DINOv2. Chapter 2 describes DINOv3 as an evaluation candidate. |
| Yassin | Owns Chapter 1. Main has a full draft with the objectives, scope, glossary, and constraints. Yassin and Ali should confirm its wording and review status. Yassin co-writes Chapter 5 with Mesbah. |
| Youssef | No commits attributable to this name in the visible history. |
| Joe | Person 3, owner of Section 3.1 System Description (not started). Review items: [`person3_joe.md`](../team-plan/review/person3_joe.md). |

History checked through `origin/main` at `22bc575` and `origin/feature/mapping-routing` at `03b3fb0`. Use Git authorship to credit specific contributions and confirm chapter ownership with the team. Add shared-document contributions when their author and section are confirmed.

## Person 6 progress

The repository has the plan, prototype evidence, and a merged editable Main draft with a prototype chapter ready for review. The submission PDF remains pending.

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
- [ ] Review Chapter 2 with Bela. Collect evidence on comparable operational tools and adopters if a market assessment is required.
- [ ] Review the provisional nonfunctional targets, hazard rule distances, and bilingual interface scope with the team and supervisor. Confirm the role wording in Section 3.1.3 against Table 3-5 and have Person 2 verify the consolidated references.
- [x] Draft the acknowledgments and add the contribution record to Appendix B. Record unresolved items in Main's editorial tracker.
- [ ] Confirm the department, formal degree title, submission month and year, name spelling and author order. Collect signatures and dates. Decide whether to include the optional dedication.
- [ ] Confirm the supervisor's decisions on chapter order, expected prototype depth, abstract length, page minimum, and submission files.

### As chapter drafts arrive

- [ ] Collect reviewed chapters and figures, merge them into the master, and make terminology, tense, headings, captions, and numbering consistent.
- [ ] Get objectives and scope from Person 1, features and limitations from Person 3, requirement IDs from Person 4, and design figures and captions from Person 5.
- [ ] Review Person 2's literature chapter for clarity, structure, and formatting. Have Person 2 review the prototype and closing sections for claims and citations. Coordinate reference order and appendices with Person 2.
- [ ] Write Chapter 5 with Yassin once the objectives and Chapter 3 drafts are agreed. Draft the roughly 200-word abstract after that and confirm the final length with the supervisor. Main keeps these sections empty until the inputs are ready.

### Before submission

- [ ] Regenerate contents and figure/table lists, check cross-references and abbreviations, and verify numbered citations in first-citation order.
- [ ] Export the PDF, inspect every page, resolve review comments, and get all six authors' approval. Hand over the editable master and the final PDF.

## Prototype evidence

Start with the [mapping prototype](../../mapping/README.md) and the committed figures. The current evidence covers 2D satellite imagery, before/after comparison, and imagery preparation. The change overlay shows pixel differences and the displayed routes are placeholders. Describe 3D views, person tracking, hazard markers, and operational route guidance as proposed capabilities unless the team supplies verified evidence. Label design illustrations as proposals and credit the source of satellite imagery.

## Keeping this file current

When report work changes an item's status, update this checklist in the same change. Mark an item complete after checking the deliverable or receiving confirmation, and add a link or commit when available. If work lives in a shared document, record its link and review status once confirmed. Record blockers beside the affected item. Fill in the ownership table as the team confirms person numbers.
