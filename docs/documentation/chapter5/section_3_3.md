<!--
Section 3.3 System Design (Person 5). Source text for the master report.
tools/build_section.py converts this file into WordprocessingML and replaces the
Section 3.3 placeholders in docs/documentation/main/Project 1 Docs.docx.

Markup used by the builder:
  ### / ####          Heading 3 / Heading 4 (numbers are written literally)
  !fig[png|caption|alt text]   figure from figures/png with its caption below
  !box[caption]                 empty bordered box for a pending visual
  Table: caption                followed by a pipe table (first row = header)
  **bold**, *italic*
Figures are numbered from 3-2 (3-1 is reserved for Person 3's workflow figure);
tables from 3-39 (Section 3.2 ends at Table 3-38).
-->

This section describes how the proposed RescueVision platform is organised to meet the requirements in Section 3.2. It covers the System Analysis and Design topics listed in the Project I guide [4]: architecture, design rationale, database and file design, user interface design, class, sequence and use case diagrams, and the detailed design of the parts that carry the most risk. Each figure is linked to the requirement and use-case identifiers of Section 3.2, and Table 3-48 at the end of the section collects those links. The design is a proposal. Diagrams describe intended behaviour, and the screen illustrations in Section 3.3.4 are design illustrations, not screenshots of working software; the evidence produced so far is reported in Chapter 4.

Two sources of notation are used throughout. Structural and behavioural diagrams follow the Unified Modeling Language (UML) 2.5.1 [27]. The architecture is described through several views (context, logical and deployment), in the manner of ISO/IEC/IEEE 42010 [28], because no single diagram can show both what the platform does and where it runs.

### 3.3.1 SYSTEM ARCHITECTURAL DESIGN

#### 3.3.1.1 Context View

Figure 3-2 places RescueVision among the people and services it depends on. Staff of the four agency types (Government, Police, EMS and Fire) use the web command console. Field responders use the mobile field application, and members of the public use the citizen request channel. All three surfaces work on one set of shared incident services. Five external parties exchange information with the platform: the drones and satellites that supply imagery (IR-HW-01, IR-HW-02), open map data that supplies building footprints and roads (IR-SW-02), a utility feed that reports whether power lines are energised where such a feed can be agreed (IR-SW-04), the push-notification services of Android and iOS (IR-SW-05), and an SMS gateway for citizen one-time codes (IR-SW-06).

!fig[fig5-01_context.png|Figure 3-2: Context view of the proposed RescueVision platform|Context diagram: agency staff, platform administrator, field responder and citizen use three client surfaces that share one set of incident services; imagery sources, open map data and a utility feed send data in; push and SMS services receive notifications.]

The context view fixes the system boundary. The platform does not fly drones or control the power network. It receives what drones capture and what a utility reports, and it treats both as inputs whose quality may vary. This boundary is the reason the design records the source and age of every observation (Section 3.3.3).

#### 3.3.1.2 Logical View

Figure 3-3 shows the main software components and the direction in which information moves between them. The design has five layers.

!fig[fig5-02_logical.png|Figure 3-3: Logical architecture of RescueVision|Layered component diagram: presentation clients, an access layer with the application interface and live-update channel, nine domain modules, a background analysis pipeline with a job queue, workers and a model registry, and a data layer with the spatial database, object storage and map-tile service.]

The **presentation layer** contains the three client surfaces. The mobile application keeps a local queue so that a responder can read tasks and record reports without coverage and send them later without duplicates (FR-FC-05, IR-CM-03).

The **access layer** has two entry points. The application interface receives every request over HTTPS (IR-CM-01), identifies the signed-in user and checks the request against the user's role and the agency's incident participation (NFR-SC-02). The live-update channel keeps a persistent connection to each client and pushes positions, alerts and case changes as they happen (IR-CM-02), so that a commander does not need to refresh a screen to see a new warning.

The **domain modules** follow the information domains of the database (Section 3.3.3): Identity and Access, Incidents and Operations, Imagery and Analysis Jobs, one module for each of the features F1 to F6, and Field and Citizen Requests. Each module owns its records and exposes operations to the others, which keeps a change to the routing rules, for example, inside the routing module.

The **analysis pipeline** runs the heavy work in the background: stitching drone images into an orthomosaic and 3D products, damage assessment, person detection and tracking, and hazard and road extraction. A request to analyse imagery becomes a job in a queue; workers with graphics processors take jobs from the queue and report progress. Every result names the model version that produced it, taken from the model registry (FR-IM-07, NFR-DQ-01).

The **data layer** holds the spatial database, which stores records, geometry, the routable road network and image embeddings, together with object storage for large files and a map-tile service that draws imagery layers for the map.

The separation between the interactive application and the analysis pipeline answers a requirement that is easy to miss: map viewing, case management and route planning must keep working when the AI service is slow or unavailable (NFR-RL-04). Because analysis runs as queued jobs, a failed or overloaded worker delays new AI layers but does not block a commander who is assigning a mission.

#### 3.3.1.3 Deployment View

Figure 3-4 shows where the components are proposed to run. It names processing nodes by their role only; the products intended for each node are described in Section 3.1.5.

!fig[fig5-03_deployment.png|Figure 3-4: Proposed deployment view|Deployment diagram: browsers and smartphones connect over TLS to an edge node, which forwards to application servers and a tile server; analysis workers with GPUs, a database server with daily backups and an object storage service complete the deployment.]

Client devices reach the platform through an edge node that terminates TLS 1.2 or later and spreads load across application servers (IR-CM-01). The analysis workers run on separate machines with graphics processors, so the most expensive hardware can be added, removed or rented without changing the application servers. Images move directly between clients, workers and object storage under short-lived signed links, which keeps large files off the application servers. The database is backed up daily to a separate location, and a restore is to be tested before the platform is used in an exercise (NFR-RL-05).

### 3.3.2 DESIGN RATIONALE AND JUSTIFICATION

The Project I guide asks for the alternatives that were considered, the reasons for the chosen design and the effect of the constraints in Section 1.7 [4]. Table 3-39 records the ten decisions that shape the architecture. Each row names the option chosen, the main alternative, the trade-off that the team accepts and the requirements the decision serves.

Table: Table 3-39: Main design decisions and their justification
| No. | Decision | Alternative considered | Reason and trade-off | Requirements |
| D-01 | One shared incident that agencies join and leave. | A separate copy of the incident for each agency, synchronised between agencies. | One record means one version of the facts and no reconciliation. Access must then be filtered per agency on every read. This follows the unity of effort described in the Incident Command System [20]. | FR-AC-04, FR-AC-05 |
| D-02 | A modular application with background workers, deployed as a small number of services. | Many independent microservices. | Fewer moving parts suit a student team and a pilot. Module boundaries follow the data domains, so a module can be separated later if load requires it. | NFR-MT-02, NFR-RL-04, NFR-PF-06 |
| D-03 | Analysis runs as queued background jobs. | Analysis inside the user's request. | Stitching and model inference can take minutes. Jobs report progress, can be retried and do not block interactive work. Results arrive later instead of immediately. | FR-IM-06, NFR-PF-05, NFR-RL-04 |
| D-04 | Access rules are enforced inside the database with row-level security, in addition to checks in the application. | Checks in application code only. | A missed check in one endpoint cannot expose another agency's incident, because the database itself filters rows [29]. Policies must be written and tested for every table. | NFR-SC-02, NFR-PV-02 |
| D-05 | Hazard rules, cost profiles, roles and permissions are stored as data. | Rules written into program code. | A new hazard combination or a new region's unit costs can be added without a software release. Rule data must be validated before it is used. | FR-HZ-13, FR-DC-09, NFR-MT-01 |
| D-06 | Published cost estimates and reports are stored as frozen snapshots. | Figures recalculated each time a report is opened. | A report that was signed or forwarded never changes silently. Storage grows with every snapshot. | FR-DC-11, FR-RP-02 |
| D-07 | Every AI result has a review state, and only a person can confirm a person, close a case or dispatch a team. | Automatic action on high-confidence results. | Model errors are expected on local data; human review keeps decisions accountable. Review adds work for Analysts, so stationary tracks and alerts are ranked first. | NFR-SF-01, FR-PD-10, FR-IM-08 |
| D-08 | The mobile application works offline and synchronises later. | An online-only application. | Networks are often damaged in a disaster area. Offline records need identifiers created on the device and duplicate checks on upload. | FR-FC-05, IR-CM-03 |
| D-09 | An open geospatial stack, with coordinates in WGS 84 and distances computed in metres on the ellipsoid. | Proprietary GIS software; distances in degrees. | No licence cost for public agencies, and rule distances such as 30 m mean the same everywhere. Geography calculations cost more than planar ones. | IR-CM-04, NFR-DQ-04 |
| D-10 | Changes are pushed to clients over a persistent connection. | Clients poll the server at intervals. | Alerts and positions reach users within seconds without repeated requests over weak links. The server must manage open connections and reconnection. | IR-CM-02, NFR-PF-02, NFR-PF-04 |

Decisions D-04 and D-07 have the largest effect on safety. D-04 means that the question "may this agency see this record?" is answered in one place for every screen and every report. D-07 keeps the platform in the role the requirements give it: it proposes, ranks and warns, and an accountable person decides.

Table 3-40 takes each constraint category of Table 1-8 in turn and states how the design responds to it.

Table: Table 3-40: How the design responds to the constraints in Section 1.7
| Constraint | Design response | Where in this section |
| Cost and economics | Open-source components (D-09); GPU workers are separate nodes that can be rented only during an incident; images that are too coarse for person detection are skipped (FR-PD-06). | 3.3.1.3, 3.3.2 |
| Environmental | Every observation keeps its source, time and uncertainty; missing or old information is shown as such, never as safe (IR-UI-06). | 3.3.3.4, 3.3.4.1 |
| Legal and ethical | Imagery and records keep their provenance and model version; an audit trail records who changed what (NFR-SC-05). | 3.3.3.4, 3.3.3.5 |
| Social | Citizens can request help from a short form; responders do not depend on a desktop; warnings use plain language (NFR-US-04). | 3.3.4 |
| Global context | Cost profiles and hazard rules are data per region (D-05), so local values replace defaults without code changes. | 3.3.2, 3.3.8.3 |
| Cultural and political | Agency and role are separate, so each agency keeps its own command structure; interface text is planned in Arabic and English with right-to-left layout (IR-UI-07). | 3.3.3.2, 3.3.4.1 |
| Health and safety | Unknown power state is treated as energised; automatic road closures can only be reversed by resolving the alert (NFR-SF-02, NFR-SF-03). | 3.3.8.2 |
| Welfare | The platform does not identify people from images (NFR-PV-03); cases record what responders need, not personal identity. | 3.3.3.5 |
| Privacy and security | Row-level security, column guards, hashed credentials and retention rules (NFR-SC-01 to NFR-SC-06, NFR-PV-01 to NFR-PV-04). | 3.3.3.5 |
| Sustainability | Results are stored once and reused by reports; old position and audit records are partitioned by month so they can be archived or removed in bulk. | 3.3.3.4 |

### 3.3.3 DATABASE DESIGN AND FILE STRUCTURES

The database is the most detailed part of the design, because every feature reads and writes the same incident. It is a relational database with spatial extensions: geometry types and spatial indexes for maps and distances [30], a routable road graph for route planning [19], and vector similarity search for comparing images. This subsection moves from the concepts to the tables. Section 3.3.3.1 explains the information model in plain terms, Sections 3.3.3.2 and 3.3.3.3 present the logical design domain by domain, and the remaining subsections cover integrity, data protection and file storage.

#### 3.3.3.1 Conceptual Information Model

Figure 3-5 shows the main categories of information and how they relate. Colour indicates the information domain each concept belongs to.

!fig[fig5-04_conceptual.png|Figure 3-5: Conceptual information model|Conceptual diagram of about twenty concepts: agency, user, team, incident, participation, mission, assignment, AI result, building, damage assessment, road segment, route, person track, assistance case, status update, hazard, compound alert, citizen request and report, linked by labelled relationships with multiplicities.]

The model is built around the **incident**. An agency takes part in an incident through a **participation**, which records whether the agency leads or supports and whether it has been invited, is active or has withdrawn. Inside the incident, each agency runs **missions**, and a mission is staffed through **assignments**, each naming either a team or a single responder, never both. A responder belongs to at most one active team at a time.

Information about the affected area comes from imagery. Analysis produces **AI results**, and every result records the model version that produced it. For buildings, a result proposes a **damage assessment**, which a person may confirm or correct; the current assessment carries a cost estimate. For people, results are person detections grouped into a **person track**.

The **assistance case** is where the person-related information meets the response. A case arises from exactly one source: a track, a verified citizen request or a responder's report. A case is handled by a mission, may be taken to a facility, and keeps a **status update** for every change. **Hazards** are recorded with their type and location. When a rule finds a dangerous combination, a **compound alert** links the hazards involved, closes the road segments inside its danger zone and invalidates the **routes** that use them. **Reports** summarise an incident for a period and keep their figures as a snapshot.

#### 3.3.3.2 Information Domains

The 56 tables of the logical design are grouped into eight domains. Table 3-41 lists them; the domain names match the modules of Figure 3-3.

Table: Table 3-41: Information domains of the RescueVision database
| Domain | Purpose | Main tables | Tables | Serves |
| D1 Identity and Access | Agencies, roles, permissions, users, sessions, devices, teams and vehicles. | agencies, users, roles, teams, vehicles | 10 | FR-AC, NFR-SC |
| D2 Incidents and Operations | The shared incident, agency participation, zones, missions and assignments. | incidents, incident_agencies, missions, mission_assignments | 6 | FR-AC, FR-MR-05 |
| D3 Imagery and Analysis | Capture sessions, images, raster products, the model registry, jobs and inference runs. | capture_sessions, images, processing_jobs, ai_models | 6 | FR-IM |
| D4a F1 Buildings and Cost | Footprints, damage assessments, cost profiles and cost estimates. | buildings, building_assessments, cost_estimates | 6 | FR-DC |
| D4b F2 Roads and Routing | The road graph, condition observations, routes and alert closures. | road_segments, routes, route_segments | 6 | FR-MR |
| D4c F3/F4 Persons and Cases | Detections, tracks, facilities, assistance cases and their events. | person_detections, person_tracks, assistance_cases | 5 | FR-PD, FR-PT |
| D4d F5 Hazards and Alerts | Hazards, infrastructure assets, hazard rules and compound alerts. | hazards, infrastructure_assets, compound_alerts | 5 | FR-HZ |
| D5 Field, Citizens, Reports and Audit | Positions, SOS, notifications, citizens and their requests, media, reports, embeddings and the audit log. | responder_positions, citizen_requests, reports, audit_log | 12 | FR-FC, FR-RP, NFR-SC-05 |

#### 3.3.3.3 Logical Design by Domain

Figures 3-6 to 3-14 present the logical design of each domain. Every table shows its columns and types; PK marks a primary key, FK a foreign key, and a question mark an optional column. Lines show relationships inside the domain in crow's-foot notation. A reference to a table in another domain is written on the column itself (for example "→ incidents"), so each figure stays readable on one page. A complete data dictionary, listing every column with its type, nullability, default value and key, is prepared for the report appendices.

!fig[fig_erd_d1.png|Figure 3-6: Logical design of domain D1, Identity and Access|Entity-relationship diagram of agencies, roles, permissions, role_permissions, users, user_sessions, user_devices, teams, team_members and vehicles.]

In D1, agency and role are independent. A user belongs to one agency and has one role, and the four roles have the same meaning in every agency. The Platform Administrator is the only user without an agency, and the database enforces this with a check that ties the role to the absence of an agency. Permissions are rows linked to roles (role_permissions), so a permission can be granted or withdrawn without changing code (NFR-MT-01). Team membership has a start and an end date, which keeps the history of who served in which team while allowing only one active membership per responder (FR-AC-07). Each vehicle records the maximum water depth it can cross, which route planning uses (FR-AC-08).

!fig[fig_erd_d2.png|Figure 3-7: Logical design of domain D2, Incidents and Operations|Entity-relationship diagram of incidents, incident_agencies, zones, missions, mission_assignments and mission_status_history.]

D2 implements the shared incident of decision D-01. The table incident_agencies is the participation record; a partial unique index allows exactly one LEAD agency per incident (FR-AC-04). An assignment must name a team or a responder but not both, which a check constraint enforces (FR-AC-06). Every change of mission status is written to mission_status_history by a trigger, with the time and the user (FR-AC-09).

!fig[fig_erd_d3.png|Figure 3-8: Logical design of domain D3, Imagery and Analysis|Entity-relationship diagram of capture_sessions, images, raster_products, ai_models, processing_jobs and inference_runs.]

In D3, a capture session groups the images of one flight or satellite pass and is labelled pre-event or post-event (FR-IM-02). Each image keeps its storage key, a SHA-256 checksum used to reject duplicates (FR-IM-03), its camera position and its ground resolution. Raster products are the orthomosaic, surface and terrain models, the 3D mesh and the AI masks. An inference run links a processing job to the exact model version it used, which is the provenance chain required by FR-IM-07. Only one model version per task can be active at a time.

!fig[fig_erd_d4a.png|Figure 3-9: Logical design of domain D4a, F1 Buildings and Cost|Entity-relationship diagram of buildings, building_assessments, cost_profiles, cost_profile_unit_rates, cost_profile_repair_ratios and cost_estimates.]

D4a separates what a building is from what happened to it. A building keeps its footprint, floors, occupancy and construction type; its floor area is computed from the footprint on the ellipsoid. Each assessment keeps the grade, the probability of each of the four xBD grades [2], the method (before/after, post-event only or field inspection) and its review state. A partial unique index keeps exactly one current assessment per building while older ones remain as history (FR-DC-06). Cost profiles hold unit costs and repair ratios per region and currency; a cost estimate copies the values it used into its own row, so later edits to the profile do not change it (FR-DC-11).

!fig[fig_erd_d4b.png|Figure 3-10: Logical design of domain D4b, F2 Roads and Routing|Entity-relationship diagram of road_nodes, road_segments, road_condition_observations, routes, route_segments and alert_closed_segments.]

D4b stores the road network as a graph of nodes and directed segments, in the form used by the pgRouting library [19]. Each segment has a current condition, a water depth, and a cost and reverse cost for each direction of travel. A negative cost marks a direction that cannot be used. Condition observations record where each report came from, and a check requires exactly one source: an AI run, a responder or a verified citizen request (FR-MR-07). A route keeps its ordered segments, which is how the platform finds the routes affected when a segment closes (FR-MR-11). The table alert_closed_segments records which alert closed which segment and the condition and costs it had before, so that resolving the alert can restore them.

!fig[fig_erd_d4c.png|Figure 3-11: Logical design of domain D4c, F3/F4 Persons and Cases|Entity-relationship diagram of person_tracks, person_detections, facilities, assistance_cases and case_events.]

D4c keeps the three levels described in Section 3.2.1.6: a detection is one sighting in one image, a track links sightings of the same person, and an assistance case is a decision by a person that help is needed. Each detection stores its confidence, visibility level, occlusion ratio, posture and a ground position with an uncertainty radius in metres (FR-PD-03, FR-PD-05). Detection rows grow quickly, so they use a block-range index on detection time. An assistance case records its source, START triage category [24], people count and status; a check links the source type to exactly one source record. Case events keep every status change, triage change, note and photo with its time and author (FR-PT-10).

!fig[fig_erd_d4d.png|Figure 3-12: Logical design of domain D4d, F5 Hazards and Alerts|Entity-relationship diagram of infrastructure_assets, hazards, hazard_rules, compound_alerts and compound_alert_sources.]

D4d holds the data for the compound-hazard rules. Infrastructure assets carry a power state of ENERGIZED, DE_ENERGIZED or UNKNOWN. Hazards carry their type, status and origin (AI, responder or citizen). A hazard rule is data: the primary hazard type, the second operand (another hazard, an asset or a road), the maximum distance, the danger buffer and whether roads close (FR-HZ-13). A compound alert stores its danger zone as a polygon, and compound_alert_sources lists the hazards and assets that triggered it, so a commander can see why the alert exists (FR-HZ-10).

!fig[fig_erd_d5a.png|Figure 3-13: Logical design of domain D5, part 1: field operations and notifications|Entity-relationship diagram of responder_positions, responder_last_positions, sos_alerts and notifications.]

The first part of D5 serves the field channel. Responder positions arrive every few seconds from every device on duty, so the table is partitioned by month and indexed by time (NFR-MT-03). A trigger keeps a separate table with only the latest position of each responder, which the command map reads (FR-FC-02). Each notification refers to exactly the record it is about (an alert, a mission, a case, an SOS or a route) through typed optional references, so a notification can be opened directly from the mobile application.

!fig[fig_erd_d5b.png|Figure 3-14: Logical design of domain D5, part 2: citizens, reports and audit|Entity-relationship diagram of citizens, citizen_requests, media_files, citizen_request_media, reports, report_shares, image_embeddings and audit_log.]

The second part of D5 keeps citizen data to the minimum allowed by NFR-PV-01: a phone number, the request and its location, and any photos the citizen chooses to attach. A trigger matches each new request to the incident whose area contains it (FR-FC-08), and a request marked DUPLICATE must point to the original (FR-FC-09). Reports keep their statistics as a snapshot, the period they cover and a disclaimer, and an approved report must name its approver (FR-RP-02 to FR-RP-05). Image embeddings store 768-value vectors with an approximate-nearest-neighbour index, which supports the optional search for visually similar past incidents (FR-RP-10) [13]. The audit log is partitioned by month like the positions.

#### 3.3.3.4 Integrity Rules

Many of the requirements in Section 3.2 are rules about what combinations of data are allowed. The design places these rules in the database, where every client must respect them. Table 3-42 lists the main rules and the mechanism that enforces each one.

Table: Table 3-42: Integrity rules enforced by the database
| Rule | Mechanism | Requirement |
| Only the Platform Administrator has no agency. | Check constraint on users. | FR-AC-02 |
| One lead agency per incident. | Partial unique index on incident_agencies. | FR-AC-04 |
| A responder is in at most one active team. | Partial unique index on team_members. | FR-AC-07 |
| An assignment names a team or a responder, not both. | Check constraint on mission_assignments. | FR-AC-06 |
| Every mission status change is recorded. | Trigger writing mission_status_history. | FR-AC-09 |
| One current damage assessment per building; grade probabilities sum to 1. | Partial unique index; check constraint; trigger retiring the previous assessment. | FR-DC-03, FR-DC-06 |
| A published cost estimate never changes. | Snapshot columns copied from the cost profile. | FR-DC-11 |
| Each road observation and each assistance case has exactly one source. | Check constraints counting non-null source references. | FR-MR-07, FR-PT-07 |
| An alert-closed road is restored only when no other active alert covers it. | alert_closed_segments with previous condition and costs; resolution function. | FR-HZ-12, NFR-SF-03 |
| Every case change is recorded with its author. | Trigger writing case_events. | FR-PT-10 |
| A duplicate citizen request points to its original. | Check constraint on citizen_requests. | FR-FC-09 |
| An approved report names its approver. | Check constraint on reports. | FR-RP-05 |
| Distances are in metres on WGS 84. | Geography casts in rules and views; SRID 4326 on every geometry column. | IR-CM-04, NFR-DQ-04 |

Two choices about volume complete the physical design. Every geometry column has a spatial index, and the two tables that grow fastest, responder positions and the audit log, are divided into monthly partitions. Old months can then be archived or deleted as whole units when the retention period ends (NFR-PV-04), without slowing the current month.

#### 3.3.3.5 Data Protection Design

Decision D-04 places access control in the database. The design uses PostgreSQL row-level security [29]: every one of the 56 tables has security enabled and denies access by default, and policies then open exactly the rows each kind of user may see. Applications never connect as the owner of the schema. Instead, each connects through one of the four group roles in Table 3-43.

Table: Table 3-43: Database roles and what they may access
| Role | Used by | Access |
| rv_app | The application interface, acting for a signed-in agency user. | Rows allowed by the policies for that user's agency, role and incident participation. |
| rv_worker | The analysis pipeline. | All operational rows; it acts for the platform, not for a user. |
| rv_citizen | The citizen request channel. | Only the citizen's own profile, requests and photos. |
| rv_readonly | Analytics and reporting. | Read-only operational data; no credentials, sessions, citizen identities or audit log. |

At the start of each request, the application interface records the identifier of the signed-in user for the duration of that transaction only, so a pooled connection cannot carry one user's identity into another user's request. Every policy derives the user's agency, role and permissions from that identifier at the time of the request. A suspended user therefore loses access on the next request, and an agency loses access to an incident as soon as its participation is withdrawn (FR-AC-05, NFR-PV-02). Draft reports remain visible only inside the authoring agency until they are approved or shared (FR-RP-04, FR-RP-06).

Policies decide which rows a user may change; column guards decide which fields. A field responder may change the status of a mission they are assigned to but not its target or priority, and users may edit their own name and phone number but not their role or agency. Password hashes cannot be read by any application role; sign-in uses a single protected function. Inserts, updates and deletes on 27 operational tables are written to the audit log with the acting user and the values before and after the change (NFR-SC-05), and no application role can modify the log (NFR-SC-06). The design will be reviewed against the OWASP Application Security Verification Standard before any field trial, as NFR-SC-07 requires [25].

#### 3.3.3.6 File Structures

Large binary files do not belong in database rows. Images, raster products, citizen photos and report PDFs are kept in object storage, and the database stores a storage key and a SHA-256 checksum for each file (IR-SW-01). Table 3-44 gives the proposed key layout. Keys begin with the incident identifier, so the files of one incident can be listed, copied or deleted together at the end of the retention period.

Table: Table 3-44: Proposed object-storage layout
| Content | Key pattern | Database record |
| Raw drone and satellite images | incidents/{incident}/captures/{session}/raw/{image}.{jpg or tif} | images |
| Orthomosaic, surface and terrain models | incidents/{incident}/captures/{session}/products/{product}.tif | raster_products |
| 3D mesh tiles | incidents/{incident}/captures/{session}/products/mesh/ | raster_products |
| AI masks (damage, change, flood) | incidents/{incident}/runs/{run}/{mask}.tif | raster_products |
| Photos from responders and citizens | incidents/{incident}/media/{media}.jpg | media_files |
| Report documents | incidents/{incident}/reports/{report}/report.pdf | reports |
| Model weights | models/{task}/{version}/ | ai_models |

Rasters are proposed as cloud-optimised GeoTIFF files so that the tile service can read only the part of a large orthomosaic that the user is viewing. Clients upload and download through short-lived signed links, and uploads can resume after an interruption (NFR-RL-03).

### 3.3.4 USER INTERFACE DESIGN

#### 3.3.4.1 Design Principles

The interface requirements in Section 3.2.2.1 lead to six design principles that apply to every screen.

Table: Table 3-45: User interface design principles
| Principle | How it appears on screen | Requirements |
| Show uncertainty openly | Every AI result shows its confidence and whether a person has reviewed it; detections show an uncertainty circle, not a single point. | IR-UI-05, FR-PD-08 |
| Show the age of information | Positions and tracks show how long ago they were observed; stale data is labelled and never shown as current. | IR-UI-06, FR-PT-05, NFR-DQ-03 |
| Never rely on colour alone | Damage grades, triage categories and alert levels carry a text label or pattern as well as a colour. | NFR-US-02 |
| Keep warnings visible | An active compound alert stays as a banner on every console screen until acknowledged; warnings state hazard, place and action. | IR-UI-04, NFR-US-04 |
| Design for the field | Large touch targets, high contrast, a one-touch SOS control and a clear offline indicator on the mobile application. | NFR-US-05, FR-FC-03 |
| Support two languages | Interface text in Arabic and English, with the layout mirrored for right-to-left reading. | IR-UI-07 |

#### 3.3.4.2 Screen Map

Figure 3-15 shows the screens of the three surfaces and the main paths between them. The incident map is the centre of the console: the detection review, the case view, the alert detail and the status board all open from it and return to it.

!fig[fig5-12_screenmap.png|Figure 3-15: Screen map of the console, mobile application and citizen channel|Navigation diagram: the console flows from sign-in to the incident list and the incident map, which leads to detection review, assistance cases, the route planner, the status board and alert detail; the mobile app flows from sign-in to missions, mission detail, case update, field report and SOS; the citizen channel flows from phone sign-in to the request form and request status.]

Table 3-46 describes each main screen, its users and the requirements it serves. The column on information states lists what the screen shows when data is missing or uncertain, since those are the situations in which a misleading screen is most dangerous.

Table: Table 3-46: Main screens and their content
| Screen | Users | Content | Information states | Requirements |
| Incident map (2D/3D) | All staff | Orthomosaic over a base map, layer panel and legend, buildings shaded by grade, detections, cases, hazards, zones, routes; 2D and 3D share the selection. | 3D view unavailable until a 3D product exists; layers without data are marked empty. | FR-MR-01 to FR-MR-04, IR-UI-03 |
| Detection review | Analyst | Image crop with box, confidence, visibility, occlusion, posture, uncertainty circle; confirm, dismiss or leave pending. | Unreviewed badge; large-uncertainty warning. | FR-PD-08 to FR-PD-10, UC-05 |
| Assistance-case view | Analyst, Commander | Source, triage, people count, mission, facility, event history; link to route planning. | Last-known-position warning with time of last sighting. | FR-PT-05 to FR-PT-12, UC-06 |
| Route planner | Analyst, Commander | Vehicle, destination, primary and alternative routes with distance and time. | "No safe route" with the blocking closures; unverified segments marked. | FR-MR-08 to FR-MR-12, UC-04 |
| Response status board | Commander | Missions, teams, assignments and cases by status; responder positions with age. | Stale positions marked after 5 minutes. | FR-AC-06, FR-FC-02, NFR-DQ-03 |
| Alert detail and banner | All staff | Rule, source hazard and asset, distance, danger zone, closed roads; acknowledge and resolve. | Unknown power state shown as treated energised. | FR-HZ-10, FR-HZ-11, IR-UI-04 |
| Report workspace | Analyst, Commander | Report type and period, frozen figures, commentary, approval and sharing, PDF export. | Coverage gaps for zones not surveyed. | FR-RP-01 to FR-RP-09, UC-08 |
| Mobile: missions and case update | Field Responder | Assigned missions, route, case triage and status, field report, SOS. | Offline indicator and count of queued items. | FR-FC-01 to FR-FC-05, UC-09 |
| Citizen request | Citizen | Phone sign-in, request type, location, photo, status. | Request received but not yet verified. | FR-FC-06 to FR-FC-10, UC-10 |

#### 3.3.4.3 Design Illustrations

Figures 3-16 to 3-22 are reserved for design illustrations of the most important screens. They will be added once the team agrees how they are produced. Each will carry the label "Design illustration, not a screenshot". Screenshots of the working prototype belong to Chapter 4 and are not repeated here.

!box[Figure 3-16: Design illustration: incident map in 2D and 3D with layers, legend and alert banner]

!box[Figure 3-17: Design illustration: a selected person detection (head only, unreviewed, with uncertainty circle)]

!box[Figure 3-18: Design illustration: assistance-case view with triage and event history]

!box[Figure 3-19: Design illustration: route guidance, including the "no safe route" state]

!box[Figure 3-20: Design illustration: response status board]

!box[Figure 3-21: Design illustration: Electrified Water alert with danger zone and closed roads]

!box[Figure 3-22: Design illustration: mobile field application with mission, SOS control and offline indicator]

### 3.3.5 CLASS DIAGRAM

The class diagrams describe the platform's main concepts as objects with responsibilities. They use the same names as the requirements in Section 3.2 and the tables in Section 3.3.3, but they show behaviour as well as data. To keep each diagram readable on one page, the model is drawn in three parts: operations (Figure 3-23), imagery and analysis (Figure 3-24), and hazards and routing (Figure 3-25). Attributes are limited to those that matter for the design; enumerations are named by type, and their values are those listed in the database design.

!fig[fig5-13_class_operations.png|Figure 3-23: Class diagram, part 1: agencies, incidents, missions and assistance cases|UML class diagram of Agency, User, Role, Team, Vehicle, Incident, Participation, Mission, Assignment, AssistanceCase, CaseEvent, Facility and Notification with attributes, operations and multiplicities.]

In Figure 3-23, filled diamonds mark composition: an incident owns its participations, missions and assistance cases, and a mission owns its assignments, so removing a mission removes its assignments. The operations carry the responsibilities of the use cases. Incident.invite() and Participation.accept() implement UC-01; Mission.assign() and Assignment.respond() implement the staffing of UC-09; AssistanceCase.verify(), assignTo() and changeStatus() carry UC-06. User.hasPermission() is the single point where a role's permissions are checked.

!fig[fig5-14_class_analysis.png|Figure 3-24: Class diagram, part 2: imagery, analysis, damage and detections|UML class diagram of CaptureSession, Image, AIModel, ProcessingJob, InferenceRun, Building, BuildingAssessment, CostEstimate, PersonDetection and PersonTrack.]

Figure 3-24 follows the provenance chain. A processing job works on one capture session and contains inference runs, each of which uses exactly one model version. Building assessments and person detections point back to the run that produced them, which answers "where did this number come from?" for every AI result (FR-IM-07). BuildingAssessment.confirm() and correct() implement the review of UC-03; correct() requires a reason (FR-DC-07).

!fig[fig5-15_class_hazards_routing.png|Figure 3-25: Class diagram, part 3: hazards, alerts, routing and reports|UML class diagram of Hazard, InfrastructureAsset, HazardRule, CompoundAlert, RoadSegment, Route, Report and the services RoutePlanner and HazardRuleEngine.]

Figure 3-25 introduces two services, which hold behaviour that belongs to no single record. HazardRuleEngine.evaluate() reads the hazard rules and raises compound alerts; CompoundAlert.resolve() reverses the closures it made. RoutePlanner.plan() searches the road segments for a vehicle and returns up to three routes (FR-MR-10). A report depends on the alerts and estimates it summarises only through its frozen snapshot, so later changes to those records cannot alter it.

### 3.3.6 SEQUENCE DIAGRAMS

The sequence diagrams show the order of messages between users and components for four of the use cases in Section 3.2.3. They were chosen because together they cover the platform's distinctive behaviour: turning AI output into a human decision (UC-06), routing under changing conditions (UC-04), the compound-hazard response (UC-07) and asynchronous analysis (UC-02). Alternative flows from the use-case narratives appear as alt fragments. The narratives themselves are not repeated; the step numbers in the diagrams are message numbers, not the step numbers of the narratives.

!fig[fig5-17_seq_uc06a.png|Figure 3-26: Sequence diagram for UC-06, part 1: reviewing a stationary track and creating an assistance case|UML sequence diagram with Analyst, Commander, console, API, cases module, database and live updates: the track is flagged, the analyst reviews it, an outdated sighting shows a warning, and a case is created or linked to an existing citizen request.]

UC-06 begins without a user action. When the database marks a track as stationary, the live-update channel highlights it on the console (FR-PT-04). Reading the track passes through row-level security, so only agencies participating in the incident receive it. If the last sighting is older than the freshness limit, the console shows a last-known-position warning before the Analyst decides (FR-PT-05). If a citizen has already reported the same person, the system offers to link the request to the existing case instead of creating a duplicate.

!fig[fig5-18_seq_uc06b.png|Figure 3-27: Sequence diagram for UC-06, part 2: assignment and field updates|UML sequence diagram with Commander, console, API, cases module, database, live updates and field responder: the commander assigns the case to a mission, the responder is notified, records triage and status, and the case is closed.]

In the second part, every change to the case writes a case event with its author, and each event is pushed to the console and the responder's device. The responder records the START triage category [24] on arrival and the receiving facility at the end, which closes the case with its full history.

!fig[fig5-19_seq_uc04.png|Figure 3-28: Sequence diagram for UC-04: planning a rescue route for a vehicle|UML sequence diagram with analyst, console, API, route planner, database, live updates and field responder: the planner excludes closed and too-deep segments, returns routes or a no-safe-route result, and later invalidates the route when a road closes.]

Route planning begins with the vehicle. The planner reads the vehicle's maximum safe water depth and builds the graph without closed segments and without flooded segments deeper than that limit (FR-MR-09). The search uses A* [18] or Dijkstra's algorithm [31] on the road graph. When no path exists, the system says so and shows the closures that block it, instead of returning an unsafe route (FR-MR-12). The final part of the diagram shows the later event of UC-04 alternative 6a: a closure invalidates the active route and the responder receives a priority warning.

!fig[fig5-20_seq_uc07.png|Figure 3-29: Sequence diagram for UC-07: responding to an Electrified Water alert|UML sequence diagram with field responder, mobile app, API, rule engine, database, live updates and commander: a flood report triggers rule evaluation, an alert closes roads, invalidates routes and notifies teams, and resolution reopens roads unless another alert covers them.]

UC-07 explains why the rule engine runs inside the platform. A single flood report from the field leads, within the 60-second target of NFR-PF-04, to a danger zone, closed roads, invalidated routes and warnings to the people inside or near the zone. The note in the diagram records the cautious default: an asset whose power state is unknown is treated as energised (FR-HZ-06, NFR-SF-02). Evaluation is idempotent, so a second report of the same flood does not raise a second alert. When the Commander resolves the alert, roads reopen only if no other active alert still covers them (FR-HZ-12).

!fig[fig5-21_seq_uc02.png|Figure 3-30: Sequence diagram for UC-02: uploading imagery and running analysis|UML sequence diagram with analyst, console, API, object storage, database job table, GPU worker and live updates: images are uploaded and registered, jobs are queued, a worker claims and runs them, reports progress, and writes results or a failure.]

UC-02 shows decision D-03 at work. The API accepts the analysis request and returns at once; the work is done by a worker that claims the next queued job. Workers claim jobs with a database lock that skips rows already taken, so several workers can share one queue without processing the same job twice. Progress is reported at least every 30 seconds (NFR-PF-05), and a failed job shows its error and can be retried, as in alternative 5a of the use case.

### 3.3.7 USE CASE DIAGRAM

Figure 3-31 gives an overview of the ten use cases of Section 3.2.3 and the actors who take part in them. The narratives, with their main and alternative flows, are in Section 3.2.3 and are not repeated here.

!fig[fig5-16_usecase.png|Figure 3-31: Use case diagram of RescueVision|UML use case diagram with actors Commander, Analyst, Field Responder, Citizen, Platform Administrator and System, connected to use cases UC-01 to UC-10 and Raise an SOS, with include and extend relationships.]

The diagram shows three relationships between use cases. UC-09 includes UC-04, because a responder carrying out a mission receives the route planned for it; UC-06 includes UC-04 for the route to a new case; and UC-05 includes UC-02, because detections exist only after analysis has run. Raising an SOS extends UC-09: it can interrupt any step of a mission when the responder is in danger. The System actor initiates UC-07, which is the only use case started by the platform itself.

### 3.3.8 DETAILED DESIGN

This subsection gives the detail needed to understand the parts of the design that carry the most risk: the life cycles of the main records, the hazard rule evaluation, the formulas behind routes, costs and positions, and the live-update events.

#### 3.3.8.1 Record Life Cycles

Figures 3-32 and 3-33 give the states of the four records whose status drives the response. Each transition is made by the actor named on it, and each is written to the record's history.

!fig[fig5-22_states_case_mission.png|Figure 3-32: State diagrams of the assistance case and the mission|UML state machines: the assistance case moves from DETECTED or VERIFIED through ASSIGNED, EN_ROUTE and ON_SCENE to RESCUED and TRANSPORTED, or ends as DECEASED or FALSE_ALARM; the mission moves from PLANNED through ASSIGNED and IN_PROGRESS to COMPLETED, or is CANCELLED.]

A case created from a track starts as DETECTED and must be confirmed before it can be assigned, which is NFR-SF-01 expressed as a state rule. A case created from a verified citizen request or a responder's report starts as VERIFIED, because a person has already checked it. Closed states (TRANSPORTED, DECEASED and FALSE_ALARM) require a closing time.

!fig[fig5-23_states_alert_report.png|Figure 3-33: State diagrams of the compound alert and the report|UML state machines: the compound alert moves from ACTIVE to ACKNOWLEDGED and RESOLVED or FALSE_ALARM; the report moves from DRAFT to PENDING_APPROVAL, back to DRAFT if changes are requested, then APPROVED and PUBLISHED.]

Only a Commander moves an alert out of ACTIVE or ACKNOWLEDGED, which is how NFR-SF-03 limits the reversal of automatic road closures. A report's figures are frozen when the draft is generated; a request for changes returns it to DRAFT, and only an approved report can be published and shared (FR-RP-04 to FR-RP-06).

#### 3.3.8.2 Compound Hazard Rule Evaluation

Figure 3-34 shows the evaluation that runs whenever a hazard or an infrastructure asset is added or changed (FR-HZ-04).

!fig[fig5-24_activity_rules.png|Figure 3-34: Activity diagram of compound hazard rule evaluation|UML activity diagram: for each active rule, find pairs within the maximum distance, skip de-energised assets, keep existing alerts, otherwise create an alert, buffer a danger zone, close roads, invalidate routes and notify responders; finally push the changes.]

Three properties of this procedure matter for safety. First, it is cautious: only an asset confirmed as DE_ENERGIZED is skipped, and UNKNOWN counts as energised. Second, it is idempotent: running it again for the same pair keeps the existing alert, so repeated reports do not flood responders with duplicate warnings. Third, it is reversible: each closed segment keeps its previous condition and costs, and resolving the alert restores them unless another active alert also covers the segment. The rule distances, such as the 30 m default for Electrified Water, are stored in the rule data and remain proposed values until the team confirms them with civil-defence or utility advice.

#### 3.3.8.3 Design Formulas

**Route cost.** Each road segment *e* has a base travel time *t*(*e*) in seconds. For a vehicle *v* with maximum safe water depth *d*(*v*), the planner uses the cost

$$ *c*(*e*, *v*) = *t*(*e*) if *e* is usable for *v*; otherwise *e* is excluded

where a segment is unusable if its condition is BLOCKED or HAZARD_CLOSED, or if it is FLOODED with water depth greater than *d*(*v*). Directions that cannot be travelled have a negative cost and are ignored by the search [19]. Segments whose condition has not been verified remain usable but are marked on the route (UC-04, alternative 3b).

**Restoration cost range.** For a building with footprint area *A*, *n* floors, damage grade *g*, and occupancy and construction type *k*, the indicative cost range is

$$ *C*_{low} = *A* × *n* × *r*_{low}(*g*) × *u*_{low}(*k*),   *C*_{high} = *A* × *n* × *r*_{high}(*g*) × *u*_{high}(*k*)

where *r*(*g*) is the repair ratio for the grade and *u*(*k*) the unit cost per square metre from the cost profile, following the repair-ratio approach of the Hazus methodology [23]. The values of *A*, *n*, *r* and *u* used are copied into the estimate as its assumptions and shown beside the figure (FR-DC-08, FR-DC-10).

**Detection position uncertainty.** A detection's ground position comes from projecting the image position through the camera position recorded for the image. Its uncertainty radius is proposed as

$$ *ρ* = √(*σ*_{GPS}^{2} + (*k* × GSD)^{2})

where *σ*_{GPS} is the horizontal accuracy reported with the image position, GSD the ground sampling distance of the image in metres, and *k* a factor, to be calibrated, for the error in projecting the detection box onto the ground. The radius therefore grows with coarser images and weaker positioning, as FR-PD-05 requires.

#### 3.3.8.4 Live-Update Events

The live-update channel (Section 3.3.1.2) carries the events in Table 3-47. Each event is delivered only to users who may see the underlying record under the rules of Section 3.3.3.5.

Table: Table 3-47: Live-update events and their recipients
| Event | Raised when | Delivered to | Requirements |
| Position update | A responder's device sends a position. | Console users of the incident. | FR-FC-02, NFR-PF-02 |
| Alert raised or resolved | The rule engine creates an alert, or a Commander resolves it. | All staff of participating agencies; priority warning to responders in or near the zone. | FR-HZ-09, NFR-PF-04 |
| Route invalidated | A segment on an active route closes. | The assigned team and the console. | FR-MR-11 |
| Case changed | A case is created, assigned or updated. | Console users; the assigned responders. | FR-PT-09, FR-PT-10 |
| Assignment | A mission is assigned to a team or responder. | The assigned responders. | FR-FC-01 |
| SOS | A responder raises an SOS. | The team leader and the Commander. | FR-FC-03 |
| Job progress | An analysis job reports progress or finishes. | The Analyst who started it. | FR-IM-06, NFR-PF-05 |

#### 3.3.8.5 Design Traceability

Table 3-48 links each figure and table of this section to the requirements and use cases it addresses. Every use case from UC-01 to UC-10 appears at least once.

Table: Table 3-48: Traceability from design elements to requirements and use cases
| Design element | Purpose | Requirements | Use cases |
| Figures 3-2 to 3-4 | Architecture: context, logical and deployment views | IR-HW-01, IR-SW-01 to IR-SW-06, IR-CM-01, IR-CM-02, NFR-RL-01, NFR-RL-02, NFR-RL-04, NFR-RL-05, NFR-PF-06 | All |
| Tables 3-39, 3-40 | Design decisions and constraint responses | NFR-SC-02, NFR-SF-01, NFR-MT-01, FR-RP-02 | All |
| Figure 3-5, Table 3-41 | Conceptual model and domains | FR-AC-04, FR-PT-07, FR-HZ-07 | UC-01, UC-06, UC-07 |
| Figures 3-6, 3-7 | Identity, incidents and operations | FR-AC-01 to FR-AC-09 | UC-01, UC-09 |
| Figure 3-8 | Imagery and analysis provenance | FR-IM-01 to FR-IM-08, IR-HW-04, NFR-MT-02, NFR-DQ-05 | UC-02 |
| Figure 3-9 | Buildings and cost | FR-DC-01 to FR-DC-13, NFR-SF-04 | UC-03 |
| Figure 3-10 | Roads and routing | FR-MR-06 to FR-MR-13, NFR-PF-03, IR-CM-05 | UC-04 |
| Figure 3-11 | Persons and cases | FR-PD-01 to FR-PD-10, FR-PT-01 to FR-PT-12 | UC-05, UC-06 |
| Figure 3-12 | Hazards and alerts | FR-HZ-01 to FR-HZ-13 | UC-07 |
| Figures 3-13, 3-14 | Field, citizens, reports and audit | FR-FC-01 to FR-FC-11, FR-RP-01 to FR-RP-10, NFR-SC-05, IR-HW-03, NFR-DQ-02, NFR-MT-03 | UC-08, UC-09, UC-10 |
| Tables 3-42 to 3-44 | Integrity, data protection, file storage | NFR-SC-01 to NFR-SC-06, NFR-PV-01 to NFR-PV-04, IR-SW-01, NFR-RL-03 | All |
| Figure 3-15, Tables 3-45, 3-46, Figures 3-16 to 3-22 | User interface design | IR-UI-01 to IR-UI-07, NFR-US-01 to NFR-US-05, NFR-PF-01, NFR-MT-04 | All |
| Figures 3-23 to 3-25 | Class diagrams | FR-AC, FR-IM, FR-DC, FR-PD, FR-PT, FR-HZ, FR-MR, FR-RP groups | All |
| Figures 3-26, 3-27 | Sequence: track to assistance case | FR-PT-04 to FR-PT-10 | UC-06 |
| Figure 3-28 | Sequence: route planning | FR-MR-08 to FR-MR-13 | UC-04 |
| Figure 3-29 | Sequence: Electrified Water alert | FR-HZ-04 to FR-HZ-12, NFR-PF-04 | UC-07 |
| Figure 3-30 | Sequence: imagery and analysis | FR-IM-01 to FR-IM-07, NFR-PF-05 | UC-02 |
| Figure 3-31 | Use case diagram | All use-case requirements | UC-01 to UC-10 |
| Figures 3-32, 3-33 | Record life cycles | FR-PT-10, FR-HZ-11, FR-RP-04 to FR-RP-06, NFR-SF-03 | UC-06, UC-07, UC-08 |
| Figure 3-34 | Rule evaluation | FR-HZ-04 to FR-HZ-08, NFR-SF-02 | UC-07 |
| Section 3.3.8.3, Table 3-47 | Formulas and live-update events | FR-MR-09, FR-DC-08, FR-PD-05, IR-CM-02 | UC-03, UC-04, UC-05 |
