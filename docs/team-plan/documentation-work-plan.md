# RescueVision — Documentation Work Plan

**Six people. Every required section. One professional graduation report.**

---

## The purpose of this guide

Divide the writing and preparation of the university documents among six people. Each assignment explains what to write, how to relate it to RescueVision, what report material to prepare, and how to check that the section is complete.

## The project idea the report describes

RescueVision is a proposed disaster-response platform for police, ambulance teams, hospitals, and other emergency organizations. Its intended website and mobile application present an affected area in 2D and 3D, show people who may need assistance and reported hazards, and support coordination and route guidance.

> The deliverables in this plan are written sections, literature comparisons, report tables, conceptual diagrams, captions, references, and a carefully assembled PDF.

Use the supplied Project I guide for required content [1] and the supplied Word template for organization and formatting [2]. Preserve the project idea while writing at the level required for the report.

Prepared for the RescueVision team | 21 October 2026. Work is ordered by document dependencies, without a timeline.

> This revised guide supersedes the previous work allocation. It assigns documentation work only.

## The revised six-person division

| Person | Writing responsibility | Main outputs |
|---|---|---|
| Person 1 | Project introduction and scope | Problem, motivation, objectives, audience, intended use, glossary and constraints. |
| Person 2 | Literature review and references | Research notes, comparison tables, related systems, research gap and bibliography. |
| Person 3 | System description | Proposed approach, features overview, user roles, assumptions, limitations and dependencies. |
| Person 4 | User and system requirements | Functional and quality requirements, interface descriptions and written use cases. |
| Person 5 | System design documentation | Conceptual organization, design explanation, diagrams and screen illustrations for the report. |
| Person 6 | Report completion and editorial control | Front matter, prototype-description section, discussion, conclusion, formatting and final checks. |

### Everyone contributes to the research

Each person reads sources relevant to their assigned sections and supplies a short note with the source, the point it supports, and the citation details. Person 2 combines these into a connected review and manages the reference list.

### Review pairings

Person 1 reviews Person 3; Person 3 reviews Person 4; Person 4 reviews Person 5; Person 5 reviews Person 1. Person 2 reviews Person 6 for claims and references; Person 6 reviews Person 2 for clarity, structure and formatting. Reviewers comment; the original author resolves the comments.

### Order of work

Agree the project wording and scope first. Build the research notes and outline next. Draft the system description, requirements and design explanations using the same terms. Merge the sections, then write the final abstract and conclusion. Finish with references, formatting and a page-by-page review.

## How the finished report should be organized

The Project I guide asks for a merged requirements/design report [1]. The Word template supplies a general chapter structure and front matter [2]. The following is a writing arrangement to confirm with the supervisor.

| Report part | What belongs there | Owner |
|---|---|---|
| Front matter | Cover, declaration, acknowledgments, abstract, contents, lists of figures/tables and abbreviations; optional dedication. | P6; P1 summary |
| Introduction | Problem, background, motivation, proposed project, objectives, scope and report organization. | P1 |
| Literature Review and Background | Research themes, related studies and systems, comparisons, market/use context, and the gap the proposal addresses. | P2 + all |
| System Description / Proposed Work | A plain-language account of the proposed approach, users, main features, assumptions and boundaries. | P3 |
| User and System Requirements | Numbered requirements, interface descriptions, use cases and quality expectations. | P4 |
| System Design | Conceptual diagrams, design choices, information relationships, screen illustrations and explanations. | P5 |
| System Prototype | Describe and label genuine preliminary material already available; explain its relevance and limits. | P6; all supply |
| Discussion, Conclusion and Future Work | Explain the proposal's value, evidence limits, objectives addressed, and remaining work. | P6 + P1 |
| References and Appendices | Numbered bibliography; extended tables, glossary, review notes and supplementary report figures. | P2/P6 |

> The Word template labels one chapter **Implementation and Testing / Experiments and Results**. For this assignment, the team prepares the written section and any available evidence; it does not perform development work. Confirm the appropriate Project I heading and depth with the supervisor.

## Person 1 — Write the introduction and project scope

### Your assigned sections

Write the report introduction and SRS 1.1 Purpose, 1.2 Intended Audience, 1.3 Intended Use, 1.4 Scope, 1.5 Definitions, 1.6 Applicable Standards, and 1.7 Constraints [1].

### What to write about RescueVision

- **Background and motivation:** explain why emergency organizations need a shared understanding of affected streets, hazards and people awaiting assistance. Support factual claims with credible sources.
- **Problem statement:** describe fragmented information, difficulty locating assistance needs, changing street conditions and coordination challenges. Avoid claiming that every organization currently works in the same way.
- **Proposed project:** explain the website, mobile application, 2D/3D area views, person tracking, hazard display and response guidance in connected prose.
- **Objectives:** state what the proposal aims to support, such as clearer incident awareness, assistance-case coordination and informed route selection. Keep objectives distinct from unmeasured achievements.
- **Scope and boundaries:** identify intended organizations, the proposed use scenario and what the report does not claim, including guaranteed hazard detection or guaranteed rescue outcomes.

### How to prepare the section

Start with a one-paragraph project definition agreed by all six. Then write from broad context to the specific RescueVision problem and proposed response. Create a scope table and a glossary so later chapters use the same vocabulary. Complete the constraint categories shown on page 10.

For 1.6, record only applicable standards/conventions agreed for the project and explain their purpose. Do not invent an adoption or compliance claim. If the supervisor must decide an item, record it as an open decision in the team review notes.

### Hand over

Introduction text; purpose/audience/use paragraphs; objectives and scope tables; glossary; constraints table; source notes; a short list of assumptions needing confirmation. Person 6 uses this material to prepare the abstract and conclusion.

> **Finished when:** a reader understands the problem, intended users, proposed value, scope and limits without reading another chapter. **Reviewer:** Person 5.

## Person 2 — Write the literature review and references

### Your assigned sections

Write Literature Review and Background, including related research, similar systems, market/use context, comparison and the proposal's justification. Maintain references for the whole report [1,2].

### What to write about RescueVision

Organize the review by questions: how disaster information is presented; how affected areas are understood in 2D/3D; how people needing assistance are identified and followed; how hazards affect movement; and how organizations coordinate a response. Discuss the research findings at the level needed to justify the proposal.

### How to research and write

- Agree research themes with Person 1. Search for relevant academic papers and official descriptions of comparable systems. Record the search terms, source, date and selection reason.
- Ask each member to submit source notes relevant to their section. Verify title, authors, publication details and the link before accepting an entry.
- For each important source, explain its purpose, approach in plain language, useful findings, limitations and relevance to RescueVision. Read beyond the abstract before making detailed claims.
- Compare several works within each theme. Identify agreements, differences and unresolved needs. End each theme by explaining what it means for the proposed project.
- Prepare a related-systems table with purpose, intended users, relevant capabilities, documented limitations and source. Mark unknown information as not established by the source.

### Hand over

A thematic chapter outline; the written review; a study-summary table; a related-systems comparison; a supported gap statement; citation details and reference list. Give every author the correct citation for their statements.

### Quality rules

Do not make the review a list of paper summaries. Do not describe a proposed capability as a proven advantage. A separate published paper is not explicitly required in the supplied course guide; the required research component is the literature review [1].

> **Finished when:** the chapter compares evidence, explains why RescueVision is worth proposing, and supports its claims with verifiable references. **Reviewer:** Person 6.

## Person 3 — Write the system description

### Your assigned sections

Write SRS 2.1 Methodology, 2.2 User Requirements and Privileges, 2.3 Assumptions / Constraints / Limitations / Dependencies, and 2.4 Intended Technologies at the report's agreed descriptive level [1].

### What to write about RescueVision

- **System overview:** describe what the proposed platform is for and how a user moves from viewing an affected area to coordinating assistance.
- **Methodology:** explain the proposed workflow in ordinary language: information is reviewed, people and hazards are presented on a map, an authorized user assesses the situation, a response is coordinated, and its status is updated.
- **Users:** describe police, ambulance staff, hospital coordinators, an incident coordinator and any agreed supporting users. Explain their goals and what each may view or change.
- **Feature overview:** explain 2D/3D views, person tracking, hazard information, route guidance and response status as user-facing capabilities.
- **Assumptions and limitations:** distinguish visible information from confirmed conditions; acknowledge incomplete, delayed or uncertain observations and the need for human judgment.

### How to prepare the section

Create a user-role table, a feature-summary table and a plain-language workflow figure. Write a short paragraph explaining each table/figure. Use Person 1's glossary and scope. Ask Person 4 to check that the feature names agree with the requirement headings.

Keep 2.4 because the course guide includes it. Describe the intended website, mobile application and mapping environment briefly. Record only choices already agreed for the written proposal; do not turn the section into a selection exercise, setup guide or development assignment.

### Hand over

System-description text; user-role/privilege table; feature-summary table; workflow figure and caption; assumptions/limitations/dependencies list; relevant source notes. Pass these to Persons 4 and 5 before their final wording is settled.

> **Finished when:** the reader can explain who uses RescueVision, what they do, and which assumptions limit the proposal. **Reviewer:** Person 1.

## Person 4 — Write the requirements and use cases

### Your assigned sections

Write SRS 3.1 Functional Requirements, 3.2 External Interface Requirements, 3.3 System Features and Use Cases, and 3.4 Nonfunctional Requirements [1]. This is a writing task describing expected behavior.

### What to write about RescueVision

Cover the agreed capabilities: viewing an incident area in 2D/3D; examining a person or hazard marker; reviewing person-tracking information; confirming an assistance need; coordinating a response; viewing route guidance; and updating response status.

### How to write each requirement

Give each requirement a unique identifier, one clear statement, its user/purpose, its priority and a way a future reviewer could judge whether it is met. Use "The system shall..." for an obligation. Keep one obligation per statement and avoid words such as easy, perfect or accurate without explanation.

For external interfaces, describe what users see, what information may be exchanged with agreed external parties, and any stated communication or equipment assumptions. Stay at the descriptive level. For quality requirements, describe clarity, accessibility, privacy, authorization, reliability and treatment of unavailable information.

### How to write a use case

Use the same template each time: title; goal; actor; starting conditions; main numbered flow; alternative situations; final state; linked requirements. Include a situation where information is uncertain or route guidance is unavailable. A complete worked writing example appears on page 14.

### Hand over

Requirements table; external-interface description; written use cases; quality-requirement table; a mapping from the project objectives to the requirements. Person 5 uses these to explain the design. Person 6 checks that important terms remain consistent.

### Keep requirements separate from design

Write what users need to accomplish and what information should be shown. Leave the report's diagrams and design explanation to Person 5. Neither assignment includes building the proposed system.

> **Finished when:** every agreed feature has clear requirements and a readable use case, with no unexplained jargon or contradictory statements. **Reviewer:** Person 3.

## Person 5 — Prepare the design chapter and diagrams

### Your assigned sections

Prepare the System Analysis and Design content requested by the course guide: conceptual architecture, design rationale, information/file organization, user interface design, class diagram, sequence diagrams, use cases and appropriate detail [1].

### What to prepare for the report

- An overall conceptual diagram showing the main functions and the relationship between the proposed website, field application and emergency users.
- A plain-language explanation of the design choices and how they address the constraints already documented by Person 1.
- An information-relationship diagram describing incidents, people requiring assistance, hazards, response assignments and status updates. Explain the meaning of the relationships in prose.
- Screen illustrations showing a 2D/3D map, a selected warning/person, an assistance-case view, route guidance and a response-status view.
- The required class/concept diagram and sequence illustrations, using the same terms and use cases as Persons 3 and 4.

### How to complete the chapter

Read the approved scope, system description and requirements before drawing. Prepare a list of figures with a purpose and related requirement for each. Draw the diagrams as editable report figures. Add a caption, explanation, source attribution where needed, and a reference from the body text.

For a sequence diagram, show the order of a user's actions and the system's expected responses. For the information/file-organization heading, explain what categories of information the report proposes and why they are related. Do not supply a physical implementation or operational instructions.

### Hand over

Written design chapter; editable diagrams and screen illustrations; figure captions; a diagram-to-requirement mapping; a short rationale for important choices. Label proposed screen illustrations clearly so they are not mistaken for screenshots of a completed product.

> **Finished when:** every diagram is explained, matches the requirements, and helps a reader understand the proposed RescueVision experience. **Reviewer:** Person 4.

## Person 6 — Complete and assemble the report

### Your assigned sections

Prepare front matter, the prototype-description section, discussion, conclusion, future work and final document assembly. Maintain formatting, figure/table numbering, contents lists and the submission checklist [1,2].

### What to write and prepare

- **Cover:** confirm the official project title, institution/department, student names, registration details where required, supervisor and submission date. Never guess missing personal details.
- **Declaration and acknowledgments:** preserve the required declaration wording, obtain each student's own details/signature, and acknowledge actual contributions. Dedication is optional.
- **Abstract:** summarize the problem, proposed response, scope and contribution after the chapters are stable. Use approximately 200 words pending confirmation of the two supplied word ranges.
- **Prototype section:** organize and caption genuine preliminary material supplied by the team. Explain what it demonstrates and what it does not establish. Do not invent screenshots, experiments or results.
- **Discussion/conclusion:** connect the report to its objectives, explain the proposal's value and limits, and distinguish completed documentation from future project work.

### How to finish the document

Create a master file with the supplied template's styles. Merge reviewed chapters, normalize terminology and tense, and update automatic contents, figures and tables. Work with Person 2 on citation order and reference consistency. Use the formatting checklist on pages 15-16.

Prepare a contribution record and unresolved-items list. Facts that only the team or supervisor can supply belong in that review list; they must not be replaced by invented statements. Export the report and inspect every page for readability and correct numbering.

### Hand over

A complete editable master, final PDF, required front matter, contents/lists, evidence captions, consistent references and a resolved editorial checklist. Confirm the requested submission files with the supervisor.

> **Finished when:** all required sections are present, consistent, readable, correctly referenced and reviewed by their owners. **Reviewer:** Person 2.

## Complete every SRS introduction heading

Use this as an authoring checklist for Person 1. Keep the course guide's heading numbers in the working SRS even if the final merged report organizes them differently [1].

| Heading | What to put in the document |
|---|---|
| 1.1 Purpose | A paragraph explaining the purpose of the requirements document and the decisions it supports. |
| 1.2 Intended Audience | Who reads it: team, supervisor, assessors and intended emergency-service stakeholders; what each needs from it. |
| 1.3 Intended Use | How RescueVision is intended to support understanding of an affected area and coordination of assistance. |
| 1.4 Scope | Problem, objectives, goals, boundaries and clear success criteria for the proposed project. |
| 1.5 Definitions | A glossary of the project's recurring terms; an overview of main features, challenges, risks and proposed mitigations. |
| 1.6 Applicable Standards | Names and purposes of standards/conventions actually agreed as applicable. Avoid unsupported compliance statements. |
| 1.7 Applicable Constraints | A table covering each category listed below, its relevance to RescueVision and its effect on the proposal. |

### Cover all of the constraint categories

Cost/economics; environment; legal and ethical responsibilities; social considerations; global context; cultural/political considerations; health and safety; welfare; privacy/security; sustainability.

For example, privacy affects how the report describes access to person-related information; language and accessibility affect how emergency users can understand warnings; environmental conditions limit what information may be available. Explain relevance without making unsupported legal or operational claims.

> **Completion check:** no required heading is silently omitted; every paragraph is specific to RescueVision; assumptions and unresolved decisions are recognizable.

## Complete the description and requirements

Person 3 owns section 2 and Person 4 owns section 3. Use this list to check coverage before merging [1].

| Heading | Writing content and completion check |
|---|---|
| 2.1 Methodology | Describe the proposed approach and main workflow. The reader should understand the sequence and purpose of the major activities. |
| 2.2 Users and Privileges | List user groups, characteristics, needs and permitted actions. Ensure the role names match every later chapter. |
| 2.3 Assumptions, Constraints, Limitations and Dependencies | Separate conditions assumed true, restrictions, known boundaries and external needs. Explain the consequence of each. |
| 2.4 Intended Technologies | Provide a brief agreed description of the intended website/mobile/mapping environment at the level requested for the report. |
| 3.1 Functional Requirements | Numbered statements covering each agreed user-facing feature; each has one meaning and a clear purpose. |
| 3.2 External Interface Requirements | Descriptive subsections for user, equipment, external software and communications interfaces, as relevant to the proposal. |
| 3.3 Features and Use Cases | Narratives explaining the main features and how users interact with them, including alternative or unavailable-information situations. |
| 3.4 Nonfunctional Requirements | Document performance expectations, safety, security and quality. Clarify any target values that still require agreement. |

### A single vocabulary across sections

Use the same names for police responders, ambulance teams, hospital coordinators, incidents, hazards, assistance cases and response status. A feature described in section 2 should have requirements in section 3 and an explanation in the design chapter.

> **Completion check:** the overview, requirements and use cases describe the same project; there are no features added in one chapter and missing from the others.

## Complete the design and prototype sections

The course guide lists the following design topics and permits adaptation to the project [1]. Person 5 documents them; Person 6 assembles the genuine preliminary evidence.

| Required topic | Documentation task |
|---|---|
| Architectural design | Draw a conceptual view of the major functions and their relationships. Explain its boundaries and intended users. |
| Design rationale | Explain alternatives considered and why the proposed organization suits the project objectives and constraints. |
| Database design / file structures | Document the information categories, their relationships and their proposed organization at the agreed report level. |
| User interface design | Provide labeled screen illustrations and explain what each user can see or do; include clear warnings and unavailable-information states. |
| Class diagram | Prepare the requested concept/class illustration and explain its main responsibilities and relationships in the report. |
| Sequence diagrams | Illustrate the order of actions/responses in selected documented use cases. Keep names consistent. |
| Use cases | Reference the complete use-case narratives from Person 4; avoid conflicting duplicate versions. |
| Detailed designs | Add only the explanatory detail needed to understand the proposal and satisfy the supervisor's report expectations. |
| System prototype | Present authentic preliminary material already available, its caption/source, what it demonstrates and its limitations. |

### Writing around figures matters

Introduce the figure before it appears, explain it afterward, and connect it to the relevant requirement or objective. A diagram without an explanation does not complete the section. Cite borrowed material; identify the team's own illustrations [2].

> When prototype evidence does not yet exist, record the missing item for supervisor review. A proposed screen illustration must be labeled as a design illustration, not presented as a working-product screenshot.

## How to work with research papers

### Read with a purpose

Use the papers to support the problem, understand related work and justify the proposal. For each selected paper, record the research question, a plain-language summary, relevant findings, limitations and the part of the RescueVision report it informs.

| Research note field | What the author records |
|---|---|
| Citation | Verified title, authors, year, publication, DOI or source link. |
| Why selected | Which report question the source helps answer. |
| Useful point | A short faithful paraphrase of the idea or finding, with its page/section for checking. |
| Limitations | What the source does not establish and which conditions limit its claims. |
| Report use | The planned chapter/paragraph and the argument this source supports. |

### Turn reading into a critical review

Compare several sources within a theme. Explain where they agree, how their aims differ, and which practical questions remain. Then connect that comparison to RescueVision. Avoid unsupported claims that the proposed project is unique or better than every existing system.

### Write and reference professionally

- Paraphrase after understanding the source. Keep the meaning, uncertainty and conditions; cite the source beside the supported statement.
- Reference figures, tables and borrowed ideas as well as direct quotations. Prefer original publications and official system descriptions.
- Keep a shared reading register so the same work is not summarized inconsistently in different chapters.
- Use numbered references in first-citation order for the final report, as required by the Word template [2].

### Is a separate paper required?

The supplied guide requires a literature review and the merged report; it does not explicitly require a journal/conference publication [1]. If the supervisor requests a separate paper, agree its scope and format first. Do not treat publication as an automatic extra deliverable.

## Examples of the writing expected

These are illustrative starting points. The assigned authors should refine them and support factual claims with sources. They are not statements that the platform has already been completed.

### Problem statement example

Emergency organizations responding to a disaster need to understand where assistance may be required and which surrounding conditions may affect access. RescueVision proposes a shared view of the affected area, combining 2D and 3D presentation with person-related observations, hazard warnings and response information. The project aims to help authorized users interpret the situation and coordinate assistance while keeping human decisions central.

### Requirement examples

| Identifier | Proposed wording |
|---|---|
| FR-01 | The system shall allow an authorized user to view the affected area in 2D and 3D. |
| FR-02 | The system shall allow the user to select a hazard marker and view its description and reported location. |
| FR-03 | The system shall display the last known information for a tracked person and indicate when that information is unavailable or outdated. |
| FR-04 | The system shall allow an authorized coordinator to update the status of an assistance case. |

### Use-case example: review an assistance case

**Goal:** understand a person-related assistance case. **Actor:** authorized coordinator. **Starting condition:** a case is available for review. **Main flow:** the coordinator selects the case, examines its location and related warnings, reviews the available information, and records the next response action. **Alternative:** information is incomplete, so the case remains pending review. **Final state:** the review outcome is recorded.

### How to know the writing is finished

Another member can understand the intended behavior, identify the user and purpose, and explain the alternative situation without asking the author to interpret the wording.

## Apply the supplied document format

These are formatting instructions for the university report, taken from the supplied Word template [2]. Apply styles consistently rather than formatting each paragraph separately.

| Element | Required treatment |
|---|---|
| Page setup | A4, single-sided; left 4 cm, right 2 cm, top/bottom 2.54 cm as shown in the template. |
| Body text | Times New Roman, 12 pt; justified; 1.5 line spacing; no first-line indentation; 12 pt before, 0 pt after. |
| Chapter label | Times New Roman italic, 14 pt; centered; 24 pt after; a new page before; use the template's spacing. |
| Chapter title / Heading 1 | Times New Roman bold, 16 pt, capitals, centered; 12 pt before, 36 pt after. |
| Main heading / Heading 2 | Times New Roman bold, 14 pt, capitals, left-aligned; 18 pt before, 12 pt after. |
| Subheading / Heading 3 | Times New Roman bold, 14 pt, title case, left-aligned; 12 pt before and after. |
| Lower headings | Heading 4: bold 13 pt. Heading 5: underlined 12 pt. Use the template's title case and 12 pt spacing. |
| Table body | Times New Roman 12 pt, left-aligned, single spacing; 6 pt before and after. |
| Figure captions | Below the figure; Times New Roman bold 10 pt, centered; 6 pt before, 24 pt after. |
| Table titles | Above the table; Times New Roman bold 12 pt, left-aligned; 12 pt before and after. |

### Keep the document easy to navigate

Generate contents, figure and table lists automatically. Number figures and tables by chapter and order, such as Figure 3-1. Refer to each figure/table in the text. Preserve image proportions and use color when needed for understanding [2].

## Front matter and editorial finishing

### Cover page checklist

Include the institution's correct name/logo, college/department, degree, project title/subtitle, team names, supervisor and submission month/year. The template specifies a centered black-and-white logo at 3.25 x 3.25 cm and detailed title-page styles; use the supplied page as the formatting reference [2].

### Required supporting pages

- **Declaration:** use the required institutional wording and collect each student's own name, registration details, signature and date.
- **Acknowledgments:** credit only real contributions. If included, a dedication follows the template's presentation.
- **Abstract:** write after the report is coherent. Summarize the problem, proposed approach, scope and value without adding unsupported outcomes.
- **Contents and lists:** update page numbers after the last edit; check every entry against the actual heading or caption.
- **Abbreviations:** list recurring abbreviations and define them on first use in the text.
- **References and appendices:** cite in the main text and include only relevant supporting material.

### Resolve the two source differences

The Project I guide asks for an abstract of approximately 150-200 words [1]; the Word template asks for 200-250 [2]. A 200-word draft fits the shared boundary; ask the supervisor which instruction governs.

The Word template specifies at least 50 main-chapter pages for the final-year report [2]. Confirm whether that applies to the Project I submission. Do not add repetitive text to reach an unconfirmed minimum.

### Edit for one consistent voice

Check terminology, tense, paragraph order, spelling and source attribution across all six contributions. Use proposed/intended wording for planned capabilities. Avoid declarations of success that are not supported by the work being reported. Preserve the institution's authorship declaration truthfully.

> **Finished when:** front matter is accurate, navigation is current, formatting is consistent, and no figure, citation or page reference is broken.

## Final handoff and submission checklist

### Each person submits the same packet

Provide your completed section text; the tables/figures it refers to; editable figure originals; captions and source credits; citation details; peer-review comments and corrections; and any facts still needing confirmation. Keep the unresolved-items list outside the finished prose until resolved.

| Check | Responsible person |
|---|---|
| Introduction, scope, glossary and all SRS 1 headings are complete. | Person 1 |
| Literature compares relevant work; references support the claims and use the required order. | Person 2 |
| All SRS 2 headings are present; users, features and boundaries are consistent. | Person 3 |
| All SRS 3 headings are present; requirements and use cases cover the agreed idea. | Person 4 |
| Design topics are explained through readable, labeled diagrams and illustrations. | Person 5 |
| Front matter, prototype description, discussion, conclusion and appendices are complete. | Person 6 |
| All chapters use the same project definition and match the two source documents. | All six |
| The editable master and final PDF have been read page by page and reviewed for submission. | Person 6; all approve |

### Three review passes

**Content:** check required headings and RescueVision relevance. **Consistency:** compare terms, objectives, requirements and figures across chapters. **Presentation:** check styles, numbering, citations, contents and every exported page.

> Start by agreeing the project definition and scope. Then give each person the section list in this guide. Completion means a reviewed contribution ready to merge into the graduation report.

## The two source documents

### [1] Project I Requirements Document Guide

College of Computing and Information Technology, Heliopolis Campus. User-supplied PDF, 3 pages.

Source file: `/home/ali/Downloads/Project I Requirements.pdf`

Used for the literature-review requirement, SRS headings 1.1-3.4, design-document topics, preliminary prototype evidence, and the required merged-report contents. Its abstract guidance is approximately 150-200 words.

### [2] Graduation Project Guidelines

User-supplied Word file titled _Project documentation-Format (1).doc_.

Source file: `/home/ali/Downloads/Project documentation-Format (1).doc`

Used for report organization, front matter, general chapter outline, typography, page settings, figure/table treatment, numbering, citation order and final-year-report length. Its abstract guidance is 200-250 words.

### Authority and interpretation

The supplied documents determine what the report must contain and how it should be presented. The six-person allocation and writing examples in this guide are proposed ways to complete that work. They are not additional university requirements.

The source files contain broad engineering headings; this guide assigns only the written explanations and conceptual report material needed to cover those headings. No development assignment is included.

### Supervisor confirmations

Confirm the final title, chapter arrangement, applicable standards, level of design detail, abstract range, whether the final-year page minimum applies to Project I, and the expected preliminary evidence. Confirm personal/institutional details before finalizing the cover and declaration.

---

_Write | Research | Review | Assemble_
