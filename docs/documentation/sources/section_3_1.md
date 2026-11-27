<!-- Section 3.1, System Description. Owner: Person 3 (Joe). Drafted for the owner's review; built by tools/build_report.py. -->
This section describes the proposed RescueVision platform in plain language: what it is for, how its users move through it, who those users are and what they may see and change, and the assumptions, constraints, limitations and dependencies that bound it. Section 3.2 turns this description into numbered requirements, and Section 3.3 shows how the platform is designed to meet them.

### 3.1.1 SYSTEM OVERVIEW

RescueVision is a proposed platform that gives Government, Police, Emergency Medical Services (EMS) and Fire agencies one shared picture of a disaster. It brings together damage seen in drone and satellite imagery, people who may need help, hazards such as floodwater near live power lines, and the state of roads, so that the agencies can decide where to send teams and how to reach them safely. The platform is designed to support people, not to replace them: every result produced by a model stays a candidate until a person reviews it.

Figure 3-1 shows the intended workflow. A Commander of the lead agency opens one shared incident and invites the other agencies. An Analyst brings in imagery, which is analysed in the background. The results appear on one map in 2D and, where suitable data exist, in 3D, each labelled with its source, its age and whether a person has reviewed it. Analysts confirm or correct what the models found. Commanders then open assistance cases and missions, assign teams and plan routes, while compound hazard alerts close roads that have become dangerous. Field Responders act on the ground and send updates, which return to the shared map. Verified citizen requests join the same list of cases, and approved reports carry the results to partner agencies.

!fig[fig3-01_workflow.png|Figure 3-1: Proposed RescueVision workflow|Workflow diagram in six steps: open the incident, bring in imagery, review the map, confirm or correct AI results, coordinate cases, missions and routes, and act and update in the field, with field updates returning to the shared map; verified citizen requests feed coordination, and approved reports are shared with agencies.]

### 3.1.2 METHODOLOGY

The platform is proposed as one web command console for agency staff, one mobile field application for responders and one short citizen request channel, all working on the same incident records. The work of an incident follows the steps of Figure 3-1. Imagery is grouped into capture sessions labelled as pre-event or post-event, so that a building can be compared before and after the disaster, or assessed from the post-event image alone when no earlier image exists. Analysis runs as tracked background jobs, and every result keeps a link to the model version and images that produced it.

Three principles shape the approach. First, one incident is shared by all participating agencies, so there is one version of the facts; each agency still runs its own missions. Second, uncertain information is shown as uncertain: a detection is a candidate, a track shows how old its last sighting is, and a route is a suggestion to be checked on the ground. Third, safety-related defaults favour caution; for example, a power line whose state is unknown is treated as energised. The six features that carry this approach are summarised in Table 3-2 and specified in Section 3.2.1.

### 3.1.3 USER REQUIREMENTS AND SYSTEM PRIVILEGES

Every user except the Platform Administrator belongs to one agency (Government, Police, EMS or Fire) and holds one role. Agency and role are independent: a Commander in the Fire agency has the same permissions as a Commander in the Police agency, applied to the incidents that the agency has joined. An agency sees an incident only while its participation in that incident is active. Only a Commander approves reports and resolves alerts. Table 3-1 describes each role; the role names match Table 3-5 in Section 3.2.

Table: Table 3-1: User roles and privileges
| Role | Characteristics | Goals | Can view | Can change |
| Platform Administrator | Technical administrator; the only user not tied to an agency. | Keep the platform, its agencies and its models correctly configured. | All agencies, incidents and configuration. | Agencies and their administrators, the AI model registry, global hazard rules; reviews citizen requests that match no incident. |
| Agency Administrator | Staff member who manages one agency’s people and equipment. | Keep the agency’s users, teams and vehicles up to date. | The users, teams and vehicles of the agency. | Users, teams and vehicles of the agency; blocks citizen accounts that submit abusive or false requests. |
| Commander | Leads the agency’s response in an incident. | Decide where teams go and keep partner agencies aligned. | All data of incidents the agency has actively joined. | Opens incidents, invites or accepts agencies, creates missions, assigns teams and cases, approves reports, acknowledges and resolves alerts. |
| Analyst | Trained staff member who works with imagery and records. | Turn imagery and reports into reviewed, trustworthy information. | All data of incidents the agency has actively joined. | Uploads imagery, runs analysis, confirms or corrects AI results, plans routes, verifies citizen requests, records infrastructure and power states, drafts reports. |
| Field Responder | Member of a team working in the affected area with a smartphone. | Complete assigned tasks safely and keep command informed. | Own missions, cases and routes, and alerts near their position. | Accepts or declines assignments, shares position, raises an SOS, updates cases and triage, sends field reports. |
| Citizen | Member of the public who signs in with a phone number. | Ask for help or report a hazard. | Own requests and their status. | Submits requests with a location and optional photos. |

Hospitals and shelters are receiving facilities in the proposed system: a case can be linked to the facility that receives the person. Hospital coordinators may be consulted as stakeholders, but they are not platform users. Table 3-2 summarises the six features and the roles that mainly use them.

Table: Table 3-2: Summary of main features
| Feature | Purpose | Main users |
| F1 Before/After Damage Assessment and Restoration Cost | Grade the damage of each assessed building and give an indicative low–high restoration cost with its assumptions. | Analyst, Commander |
| F2 2D/3D Mapping and Rescue Route Planning | Show one georeferenced map in 2D and 3D and plan routes that avoid closed or too-deep flooded roads for the chosen vehicle. | Analyst, Commander, Field Responder |
| F3 Aerial Person Detection under Partial Visibility | Mark candidate locations of people seen from the drone, including partly hidden people, each with a position uncertainty. | Analyst |
| F4 Multi-Object Person Tracking and Assistance Cases | Follow the same person across images and manage each confirmed case from first sighting to its outcome. | Analyst, Commander, Field Responder |
| F5 Compound Hazard Alerts (“Electrified Water”) | Warn teams and close roads when floodwater lies near a power line that is not confirmed de-energised. | Commander, Field Responder |
| F6 General Reports | Produce frozen, approved reports that agencies can share. | Analyst, Commander |

### 3.1.4 ASSUMPTIONS, CONSTRAINTS, LIMITATIONS AND DEPENDENCIES

The four lists below are kept separate. Each item states what happens if it does not hold.

#### 3.1.4.1 Assumptions

**Drone images carry GPS metadata.** Images are expected to include the camera position, altitude and capture time. If they do not, the Analyst must supply the location by hand (FR-IM-04), and images without a usable location cannot be placed on the map.

**Notification and SMS services are available.** Push notifications to the mobile application and SMS one-time codes for citizens are assumed to work in the affected area. If they fail, responders receive tasks only when they open the application, and citizens cannot sign in.

**A utility power-state feed is optional.** Where the utility can provide one, power states update automatically; otherwise an authorised user enters them by hand (IR-SW-04). Without timely updates, more power lines stay in the unknown state and are treated as energised, which closes more roads than necessary.

**Rule distances and thresholds are provisional.** The Electrified Water distance (proposed default 30 m), the freshness limits and the other configured values are working proposals. If civil-defence or utility guidance differs, the stored rule values must be changed before any operational use.

**Targets are proposals.** The performance and quality targets in Section 3.2.4 are proposed for a future evaluation. If the supervisor or partner agencies set different targets, the requirements are updated before testing.

#### 3.1.4.2 Constraints

**A student team with limited time.** The project is built and documented by six students within the Project I and Project II terms. Features beyond the agreed scope are left for future work rather than delivered partially.

**Limited computing.** Training uses free or team-owned graphics processors, and the demonstration server runs models on a CPU only. Analysis is therefore slower than in the proposed deployment, and large image sets are processed as queued jobs.

**Open data only.** Imagery, building footprints and road data come from open sources such as Maxar Open Data, OpenStreetMap and Overture. Their coverage, date and licence limit where and how the platform can be demonstrated; the Maxar imagery is licensed for non-commercial use.

**No live integration with outside systems.** The project does not connect to government, hospital or dispatch systems. Exchanges with them are described as interfaces (Section 3.2.2) and demonstrated with prepared data.

#### 3.1.4.3 Limitations

**AI outputs are candidates.** Every model result needs human review before it is acted on. If reviewers are overloaded, results wait; the design ranks stationary tracks and alerts first to reduce the delay.

**A detection is not a confirmed person.** False alarms and missed people are expected. A person becomes an assistance case only when an Analyst confirms the detection or a verified report supports it.

**People under rubble are out of scope for F3.** Aerial imagery cannot see people buried in collapsed buildings; such people can only enter the platform through citizen or responder reports.

**Observations may be incomplete, delayed or uncertain.** Imagery may be hours old, positions have an uncertainty in metres, and some roads have no verified condition. The interface shows the age and source of each item so that users can judge it.

**An unknown power state is treated as energised.** This keeps responders safe but may close roads that are in fact passable until the utility confirms the line is off.

**Cost estimates are indicative.** They depend on local unit costs and repair ratios entered by users and on the damage grade. They are not engineering surveys or insurance valuations.

**The platform neither flies drones nor controls the power network.** It receives imagery and power states; operating drones and switching power remain with their owners.

**The targets in Section 3.2.4 are not measured results.** No accuracy or speed figure in this report has yet been measured on the platform.

#### 3.1.4.4 Dependencies

**Object storage** holds images, rasters, 3D products and reports. Without it, uploads and results cannot be stored.

**OpenStreetMap or Overture data** supply building footprints and the road network. Where the open data are incomplete, footprints must be extracted from imagery or drawn by hand, and routing is limited to the roads that exist in the data.

**The AI inference service** runs the damage, detection and tracking models. If it is unavailable, new AI layers are delayed, but map viewing, case management and routing continue (NFR-RL-04).

**Push-notification services** of Android and iOS deliver alerts and tasks to the mobile application.

**An SMS gateway** sends citizen one-time codes. Without it, the citizen channel is closed.

**An optional utility feed** supplies power states. Without it, power states are entered by hand (IR-SW-04).

### 3.1.5 INTENDED TECHNOLOGIES

The web command console is intended to be a single-page browser application built with React and Vite, for desktop browsers. The mobile field application is intended to be built with Expo (React Native) for Android and iOS, with offline storage on the device so that tasks and reports can be kept while the network is down. Both use one map engine, MapLibre GL, for the 2D map; the 3D view draws building shapes and precomputed 3D tiles produced from drone imagery with OpenDroneMap. The citizen channel is a short mobile form.

All three surfaces call one application interface built with FastAPI, which sends live changes to connected clients. Records are stored in PostgreSQL 18 with PostGIS 3.6 for geometry, pgRouting for route planning on the road network and pgvector for image embeddings. Row-level security in the database limits each agency to the incidents it has joined. Coordinates are stored in WGS 84, and distances are computed in metres. Large files are kept in S3-compatible object storage, and push-notification and SMS services deliver messages. The AI models run as separate services behind a job queue. For the Project II demonstration they are planned to run with ONNX Runtime on a single CPU server; the graphics processors in the deployment view of Section 3.3 describe the proposed configuration for an operational deployment.
