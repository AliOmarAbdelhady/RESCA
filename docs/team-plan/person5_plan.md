# Person 5 Plan: Section 3.3, System Design

**Owner:** Ali (Person 5). **Reviewer:** Person 4. **Feeds:** Person 6 (assembly, list of figures).
**Status:** implemented in `docs/documentation/main/Project 1 Docs.docx`, 23 November 2026. Sources in `docs/documentation/chapter5/`.

## 1. What the chapter must achieve

The Project I guide asks for the System Analysis and Design content of the SDD: architectural
design, design rationale, database design and file structures, user interface design, class
diagram, sequence diagrams, use cases and detailed designs. It also asks the team to show how the
design responds to the constraints in Section 1.7 [Project I guide, p. 3].

Section 3.3 is finished when a reader can do three things without help:

1. Explain how RescueVision is organised and why it is organised that way.
2. Follow any requirement in Section 3.2 to the diagram and design decision that satisfies it.
3. Tell proposed design illustrations apart from screenshots of working software.

## 2. Scope boundary

The [six-person work plan](documentation-work-plan.md) gives Person 5 the design section (3.3) only.
Everything in this plan traces to its Person 5 assignment or to the System Analysis and Design list
in the course guide.

| In scope (Person 5) | Out of scope (owner) |
|---|---|
| Architecture, rationale, information design, UI design, class, sequence and use case diagrams, detailed design, captions, diagram-to-requirement mapping | Requirement statements and use-case narratives (Person 4, Section 3.2); Section 3.3 references them by ID and does not rewrite them |
| Screen **design illustrations**, labelled as proposals | Screenshots of working software and prototype evidence (Person 6, Chapter Four, System Prototype) |
| Naming the components of the design | Choosing products, languages and frameworks (Person 3, Section 3.1); Section 3.3 refers to that section |
| Source notes for figures that borrow notation or ideas | The reference list and citation order (Person 2) |
| Reviewing Person 1's chapter | Front matter, assembly and the final PDF (Person 6) |

## 3. Inputs and the vocabulary the chapter must reuse

| Input | Source | What Section 3.3 takes from it |
|---|---|---|
| Objectives OBJ-01 to OBJ-06; constraints Table 1-8 | Chapter 1 (Main draft) | Rationale links; constraint-to-design table |
| Roles, workflow, technologies (SRS 2.1 to 2.4) | Section 3.1 (Person 3) | Actor names, intended technologies |
| FR-, IR-, NFR- identifiers; UC-01 to UC-10 | Section 3.2 (Person 4) | Every figure is mapped to these IDs |
| Approved data model (56 tables, 8 domains, RLS) | `database/`, design spec, draw.io ERD | Information design, class diagram, security design |
| Brand identity (navy, cyan, amber) | `docs/brand/identity/` | Screen illustrations |

Fixed vocabulary: Platform Administrator, Agency Administrator, Commander, Analyst, Field Responder,
Citizen, System; agency types Government, Police, EMS, Fire; incident, participation, mission,
assignment, capture session, detection, track, assistance case, hazard, infrastructure asset,
compound alert, road segment, route, report. Damage grades follow xBD; triage follows START.

## 4. Chapter outline and figures

Figures and tables are numbered for the merged report (Section 3.3 follows Person 3's Figure 3-1 and Person 4's Tables 3-3 to 3-38). Each is introduced in the text, shown,
explained, and linked to requirement IDs.

### 3.3.1 System Architectural Design
- **Figure 3-2 Context view.** Users and agencies, the three client surfaces (web command console,
  mobile field application, citizen channel), and the external services in IR-SW-01 to 06.
- **Figure 3-3 Logical architecture.** Clients, the API with its live-update channel, the domain
  modules (one per data domain), the analysis pipeline running as background jobs, and the
  spatial database and object storage.
- **Figure 3-4 Deployment view.** Proposed processing nodes named by role (web client hosting,
  application server, analysis workers with GPUs, spatial database, object storage, map-tile
  service). It names no products; those come from Section 3.1 (Person 3).
- Prose: responsibility of each component, the boundaries, and why map viewing, cases and routing
  keep working when the AI service is down (NFR-RL-04).

### 3.3.2 Design Rationale and Justification
- **Table 3-39 Design decisions.** Each row gives the decision, the alternatives considered, the
  reason for the choice, the trade-off accepted, and the constraint and requirement IDs. Planned
  rows:
  1. One shared incident that agencies join (alternative: separate copies per agency).
  2. A modular monolith plus background workers (alternative: microservices).
  3. Asynchronous analysis jobs kept apart from the interactive API.
  4. Access enforced in the database with Row-Level Security, not only in application code.
  5. Hazard rules, cost profiles and permissions stored as data.
  6. Snapshots for published cost estimates and reports.
  7. Human review states for every AI result.
  8. Offline-first mobile application.
  9. Open geospatial stack and WGS 84 coordinates with distances in metres.
  10. Push updates over a persistent connection instead of polling.
- **Table 3-40 Constraints and the design response.** Covers all ten categories in Table 1-8, as
  the course guide requires.

### 3.3.3 Database Design and File Structures
This is the most detailed subsection, because the approved data model is the
project's most complete design artefact.
- **Figure 3-5 Conceptual information model.** About 18 core concepts and their relationships,
  with each relationship explained in prose (for example, "an assistance case may arise from a
  track, a citizen request or a responder report, and from exactly one of them").
- **Table 3-41 The eight information domains:** purpose, main entities, table count, and the
  features they serve.
- **Figures 3-6 to 3-14 Logical ERD, one per domain (D4 and D5 split for A4):** entities, keys, relationships and
  cardinalities, generated from the live catalog with PlantUML. Each is followed by an
  explanation of its design choices.
- **Integrity rules (Table 3-42):** one current assessment per building with history kept,
  exactly-one-source records, a responder in one active team, one lead agency per incident,
  snapshots of cost estimates and reports, and the audit trail. Each rule is linked to its
  requirement.
- **Spatial design:** coordinate reference WGS 84 (IR-CM-04), distances in metres
  (NFR-DQ-04), spatial indexing, the road network as a routable graph, and partitioning of
  high-volume position records (NFR-MT-03).
- **Data protection design (Table 3-43, database roles):** the four database roles, agency isolation by incident
  participation, column guards, the audit trail, and the privacy rules NFR-PV-01 to 04 and
  NFR-SC-02, 05 and 06.
- **File structures (Table 3-44):** object-storage layout for raw images, orthomosaics, 3D
  products, media and report PDFs; storage key and checksum (IR-SW-01); retention (NFR-PV-04).
- **Appendix material:** a data dictionary (every table and column with its type and meaning),
  generated as `docs/documentation/chapter5/appendix_data_dictionary.md` and supplied to Person 6 for the appendices.

### 3.3.4 User Interface Design
- Design principles (Table 3-45): uncertainty shown openly, freshness labels, colour never used alone, a
  persistent alert banner, Arabic and English with right-to-left layout (IR-UI-01 to 07,
  NFR-US-01 to 05).
- **Figure 3-15 Screen map** of the web command console, the mobile field application and the
  citizen channel, showing how the user moves between screens.
- **Table 3-46 Screen descriptions:** for each screen, its user, its purpose, what is shown, the
  uncertainty and unavailable-information states, and the requirement IDs.
- **Figures 3-16 to 3-22 Design illustrations.** Slots are reserved now and stay empty until the
  team decides how to produce them: the 2D/3D incident map, a selected person detection, the
  assistance-case view, route guidance including the no-safe-route state, the response status
  board, the Electrified Water alert state, and the mobile field application. When filled, each
  image carries the label "Design illustration, not a screenshot".
- Screenshots of the working prototype are **not** added here. They belong to Person 6's System
  Prototype chapter (Chapter Four), and Section 3.3 may cross-reference them.

### 3.3.5 Class Diagram
- **Figures 3-23 to 3-25 Domain class diagrams:** about 20 classes with key attributes, responsibilities
  such as `Incident.invite()`, `AssistanceCase.changeStatus()`, `CompoundAlert.resolve()` and
  `RoutePlanner.plan()`, multiplicities, and enumerations. Split into an operations view, an imagery and analysis view, and a hazards and routing view.
- Prose: the responsibility of each class group.

### 3.3.6 Sequence Diagrams
Four use cases are chosen to cover the signature behaviour. `alt` fragments show Person 4's
alternative flows.
- **3-26 and 3-27 UC-06** Turn a stationary track into an assistance case.
- **3-28 UC-04** Plan a rescue route (no-safe-route and route-invalidated alternatives).
- **3-29 UC-07** Electrified Water alert, from the field report to the roads reopening.
- **3-30 UC-02** Upload imagery and run analysis (asynchronous jobs, progress, failure).

### 3.3.7 Use Case Diagram
- **Figure 3-31:** UML use case diagram for UC-01 to UC-10, with actors, the system boundary and
  include/extend relationships. The text references the narratives in Section 3.2.3 and does not
  duplicate them.

### 3.3.8 Detailed Design
- **3-32 and 3-33 State diagrams** for the assistance case, mission, compound alert and report.
- **3-34 Activity diagram** of compound-hazard rule evaluation (buffer, close roads, invalidate
  routes, notify).
- Design formulas: the vehicle-aware route cost (closed and too-deep segments excluded), the
  restoration cost range (area × floors × repair ratio × unit cost), and the detection
  uncertainty radius.
- **Table 3-47** Live-update events (positions, alerts, case changes) and who receives them.

### 3.3.8.5 Traceability
- **Table 3-48:** each figure and table, its purpose, and the FR/IR/NFR/UC IDs it covers. Every
  UC-01 to UC-10 appears at least once.

## 5. How the work is produced

| Step | Output | Check |
|---|---|---|
| 1. Vocabulary and ID sheet | One-page term list matched to Chapters 3 and 4 | No term differs between chapters |
| 2. Diagrams (drawn by Claude; bulk rendering may be delegated to Sonnet 5.5 at medium effort) | PlantUML sources in `docs/documentation/chapter5/figures/src/` with 200 dpi PNG exports (`render.sh`) | Readable at A4 width, 10 pt minimum text, UML notation |
| 3. Screen design | Screen map and screen descriptions now; illustration slots left empty until the team decides | No screenshots of working software in Section 3.3 |
| 4. Prose | Chapter text in Markdown for review | Every figure introduced and explained, with IDs cited |
| 5. Into the master | Section 3.3 in `Project 1 Docs.docx` via `chapter5/tools/build_section.py` | Captions 10 pt bold centred; Times New Roman 12 pt; justified, 1.5 spacing |
| 6. Review | Person 4 review; comments resolved | Traceability table complete |

Writing standard: formal, precise and plain. Proposed behaviour is written as "is designed to" or
"is intended to", never as achieved. Each claim is backed by a requirement ID or a citation, and
there are no marketing adjectives. Citations use IEEE numbers coordinated with Person 2.

## 6. Open items for the team or supervisor

- Person 4's section says PostgreSQL 16; the implemented database targets PostgreSQL 18 (it uses
  native `uuidv7()`). Person 4 should update the Basis line.
- "Hospital coordinator" is not a user role in the data model; hospitals are facilities. Agree the
  wording with Persons 3 and 4.
- Confirm the depth of database detail for the body versus the appendix with the supervisor.
- Section 3.3 names components only. If the supervisor wants products shown in the deployment
  view, they must match Person 3's Section 3.1.

## 7. Hand-over packet

Section 3.3 text (`section_3_3.md`); PlantUML sources and PNG exports; captions; Table 3-48 traceability;
data dictionary for the appendix; rationale table; open-items list; reference notes for Person 2.
