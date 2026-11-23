# RescueVision repository guidance

## Current focus

Work on the Project I graduation report. Keep changes to report material, evidence, and editorial coordination. Change application code or run new experiments only if the user explicitly changes the scope.

Use the [team documentation plan](docs/team-plan/documentation-work-plan.md) for assignments and [Mesbah's Person 6 plan](docs/team-plan/person6_plan.md) for the detailed outline and formatting checklist. Use the university requirements guide and Word template when available.

## Local report workspace

- Put the Selection Word export in [`docs/Documention/selection/`](docs/Documention/selection/) and the Main Word export in [`docs/Documention/main/`](docs/Documention/main/). Keep the original filenames so the two versions can be compared.
- Keep the university template and requirements guide in `.local-report/source/` and use `.local-report/working/` for edits. Confirm the team's master before working from it.
- For layout, preserve the university template specified in the team plan. For citations, use IEEE bracketed numbers in first-citation order and reuse the same number for each source. Confirm with the supervisor if an IEEE publication template is also expected.
- New Word exports and local drafts are Git-ignored by default. The two original snapshots under `docs/Documention/` were explicitly selected for Git. Merge local edits into the shared report after checking the latest team copy.

### Report versions

- [Selection](<docs/Documention/selection/Project 1 Docs — Skeleton (Marwan draft).docx>) has the seven project chapters, including Chapter 6 System Prototype and Chapter 7 Discussion, Conclusion and Future Work. Most sections contain author prompts and figure placeholders. The original Selection snapshot is in commit `dac7162`.
- [Main](<docs/Documention/main/Project 1 Docs.docx>) is the merged local working draft. It combines Selection's seven-chapter structure with Main's authored Chapter 1, eight tables, and five numbered references. The previous Main snapshot is in commit `dac7162`.
- Use the same margins as page 1 throughout the working report, including equal 2.54 cm left and right margins. Keep the declaration signatures in one two-column table.
- Each DOCX has an editable `.source/` folder beside it. Edit `package/word/document.xml` for content or `package/word/styles.xml` for styles, then run `python3 docs/Documention/build_docx.py build "<path to DOCX>"`. After editing directly in Word, run the same command with `extract` to refresh the corresponding source package.
- The System Prototype chapter still needs prose, figures, captions, and citations. Refresh the contents and caption lists in Word after editing and before exporting the submission PDF.

## Team and report ownership

Team roster: Mesbah, Mahmoud, Ali, Bela, Yassin, and Youssef. Mesbah is confirmed as Person 6 by the owner line in his plan. The names for Persons 1–5 still need team confirmation.

| Person | Confirmed owner | Report responsibility | Reviewed by |
| --- | --- | --- | --- |
| 1 | Pending | Introduction, objectives, scope, glossary, and constraints. Co-writes the closing sections with Mesbah. | Person 5 |
| 2 | Pending | Literature review, related systems, research gap, and references. Coordinates appendices and citations with Mesbah. | Mesbah |
| 3 | Pending | System description, proposed workflow, user roles, assumptions, and limitations. | Person 1 |
| 4 | Pending | Functional and quality requirements, interfaces, and written use cases. | Person 3 |
| 5 | Pending | System design chapter, diagrams, design rationale, and screen illustrations. | Person 4 |
| 6 | Mesbah (Marwan Mesbah) | System Prototype chapter, front matter, closing sections with Person 1, and final report assembly and review. | Person 2 |

### Contributions verified in Git

| Teammate | Contribution or current evidence |
| --- | --- |
| Mesbah | Authored the mapping prototype and research notes (`f0b600f`), then the Person 6 plan and six prototype figures (`03b3fb0`). Git records his name as `Marwan` and `Marwan Mesbah`. |
| Ali | Authored the six-person documentation work plan (`22bc575`) and merged the mapping branch into `main` (`6bb10b4`). Git records his name as `AliOmarAbdelhady`. His assigned report section is pending confirmation. |
| Mahmoud | No commits attributable to this name in the visible history. |
| Bela | No commits attributable to this name in the visible history. |
| Yassin | No commits attributable to this name in the visible history. |
| Youssef | No commits attributable to this name in the visible history. |

History checked through `origin/main` at `22bc575` and `origin/feature/mapping-routing` at `03b3fb0`. Use Git authorship to credit specific contributions and confirm chapter ownership with the team. Add shared-document contributions when their author and section are confirmed.

## Person 6 progress

The repository has the plan, prototype evidence, and a merged editable Main draft. The finished prototype chapter and submission PDF have yet to be produced.

- [x] Commit the 2D satellite mapping prototype (`f0b600f`).
- [x] Commit the Person 6 plan and six [prototype figures](docs/team-plan/figures/) (`03b3fb0`).

### Start now

- [x] Merge the Word reports into one editable Main draft with heading styles and contents and figure/table fields.
- [ ] Check the editable draft against the university requirements guide and complete the abbreviations list.
- [ ] Draft the System Prototype chapter using the existing figures. Explain its purpose, imagery and study area, 2D map and comparison views, data preparation, and limitations. Add captions and imagery credits, refer to each figure in the text, and add requirement IDs once Person 4 supplies them.
- [ ] Draft the cover, declaration, and acknowledgments. Confirm the official project and institution details and collect the team details and signatures required by the template.
- [ ] Start a contribution record and an open-items list. Track supervisor decisions on chapter order, expected prototype depth, abstract length, page minimum, and submission files.

### As chapter drafts arrive

- [ ] Collect reviewed chapters and figures, merge them into the master, and make terminology, tense, headings, captions, and numbering consistent.
- [ ] Get objectives and scope from Person 1, features and limitations from Person 3, requirement IDs from Person 4, and design figures and captions from Person 5.
- [ ] Review Person 2's literature chapter for clarity, structure, and formatting. Have Person 2 review the prototype and closing sections for claims and citations. Coordinate reference order and appendices with Person 2.
- [ ] Write the discussion, conclusion, and future work with Person 1 once the chapters are stable. Draft the roughly 200-word abstract after that and confirm the final length with the supervisor.

### Before submission

- [ ] Regenerate contents and figure/table lists, check cross-references and abbreviations, and verify numbered citations in first-citation order.
- [ ] Export the PDF, inspect every page, resolve review comments, and get all six authors' approval. Hand over the editable master and the final PDF.

## Prototype evidence

Start with the [mapping prototype](mapping/README.md) and the committed figures. The current evidence covers 2D satellite imagery, before/after comparison, and imagery preparation. The change overlay shows pixel differences and the displayed routes are placeholders. Describe 3D views, person tracking, hazard markers, and operational route guidance as proposed capabilities unless the team supplies verified evidence. Label design illustrations as proposals and credit the source of satellite imagery.

## Keeping this file current

When documentation work changes an item's status, update this checklist in the same change. Mark an item complete after checking the deliverable or receiving confirmation, and add a link or commit when available. If work lives in a shared document, record its link and review status once confirmed. Record blockers beside the affected item. Fill in the ownership table as the team confirms person numbers.
