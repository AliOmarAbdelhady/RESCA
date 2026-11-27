<!-- Chapter 5, Discussion, Conclusion and Future Work. Owners: Person 1 (Yassin) and Person 6 (Mesbah). Drafted for the owners' review; built by tools/build_report.py. -->
This chapter discusses how far Project I meets the objectives set in Chapter 1, states the limitations of the work, draws conclusions and sets out the work planned for Project II. It separates what the report specifies and designs from what the evidence so far shows.

## DISCUSSION

Project I set six objectives (Table 1-2). For each one, the report now contains requirements in Section 3.2, linked in Table 3-38, and design elements in Section 3.3, linked in Table 3-48. Prototype evidence in Chapter 4 covers only part of the first two objectives. The discussion below takes each objective in turn.

**OBJ-01, a consistent spatial view in 2D and 3D.** The requirements specify one georeferenced map with the same layers in 2D and 3D and a selection that survives switching between them (FR-MR-01 to FR-MR-05). Section 3.3 places the map at the centre of the console and stores all geometry in one coordinate system. The prototype in Chapter 4 shows two dated satellite images of the same area in one 2D frame and a synchronised side-by-side view; it does not show a base map, an orthomosaic or a 3D view. The objective is therefore specified and designed, and partly demonstrated in 2D.

**OBJ-02, damage and indicative cost linked to their evidence.** The requirements specify four damage grades with their probabilities, a label for the assessment method, review by an Analyst and a low–high cost range with visible assumptions (FR-DC-01 to FR-DC-13). Every AI result keeps its model version and input images (FR-IM-07), which answers the provenance gap identified in Chapter 2. The prototype shows a pixel-change layer over a dated image pair, but no damage grades, confidence values or costs. No model has yet been trained or evaluated on project data.

**OBJ-03, people who may need help and hazards, including compound hazards.** The requirements treat every aerial detection as a candidate with a position uncertainty in metres (FR-PD-01 to FR-PD-10), follow people across images into tracks and assistance cases (FR-PT-01 to FR-PT-12) and specify the Electrified Water rule, which treats an unknown power state as energised (FR-HZ-01 to FR-HZ-13). Section 3.3 gives the case and alert life cycles and the rule evaluation. Chapter 2 found that compound hazards are recognised in hazard research but not acted on by the systems reviewed; RescueVision addresses this in its design, but no part of OBJ-03 has yet been demonstrated.

**OBJ-04, coordination across agencies.** The requirements and design centre on one shared incident that a lead agency opens and others join, with common roles across agencies, missions per agency and reports that a Commander approves before they are shared (FR-AC-01 to FR-AC-11, FR-RP-01 to FR-RP-11). Database row-level security is designed to keep each agency to the incidents it has joined. This responds to the coordination obstacles reported in the literature, but whether it improves coordination can only be shown with users.

**OBJ-05, informed route selection.** Routing is specified per vehicle, excluding closed segments and floodwater deeper than the vehicle can cross, with an explicit no-route result and re-planning when a road closes (FR-MR-06 to FR-MR-13). The design uses graph search on the road network inside the database. The prototype’s route symbols are placeholders, so no route has yet been computed.

**OBJ-06, visible uncertainty and enforced permissions.** Requirements on confidence, review state, data age and permissions (IR-UI-05, IR-UI-06, NFR-DQ-01, NFR-DQ-03, NFR-SC-02) are reflected in the design’s review states and access rules. They are untested.

Taken together, Project I delivers a consistent specification and design for all six objectives, with requirement and design identifiers linked from objective to diagram, and preliminary visual evidence for two of them. The proposal responds to each of the four gaps identified in Section 2.9: a design for transfer testing, provenance and visible uncertainty, joined people-finding channels and compound hazard alerts. None of these responses has yet been tested.

## LIMITATIONS

**No measured results.** No model has been trained or evaluated on project data, and no performance target in Section 3.2.4 has been measured. Every number in the requirements is a proposal.

**Limited prototype evidence.** The prototype covers one urban area of about 0.8 × 0.8 km and two acquisition dates. Its change layer is a pixel-difference illustration whose method is not yet documented in the repository, so it supports no damage claim.

**Data quality and local accuracy.** The public datasets cover a few events and regions, and models trained on them may perform worse on local buildings. Map position depends on GPS and ground control, and may be wrong by metres.

**Human review of every AI result.** The design relies on Analysts to review detections, grades and tracks. In a large incident the review workload could delay decisions; the design ranks stationary tracks and alerts first, but this has not been tested.

**Privacy of person data.** Detections, tracks and citizen requests describe vulnerable people. The design limits access to participating agencies and sets retention rules, but the retention period and legal basis still have to be agreed.

**Unknown power states.** Treating an unknown power state as energised is safe but may close passable roads until the utility confirms a line is off.

**No user evaluation.** No emergency-service user has yet tested the interface or the workflow.

## CONCLUSION

Responding agencies need to know quickly which buildings are damaged, where people may need help, which hazards make roads dangerous and how to reach those people, and they need to share that picture with each other. Chapter 2 showed that research and operational systems address these needs separately, rarely show how uncertain each output is and do not act on combined hazards such as floodwater near live power lines.

Project I responds with a specification and design for RescueVision. The report defines six objectives and six features, 167 uniquely identified requirements and ten use cases, and a design that links each requirement to its architecture, data and interface elements. The design keeps one shared incident for all agencies, treats every AI result as a candidate until a person confirms it, keeps the provenance of every result and raises compound hazard alerts that close roads and re-plan routes.

The evidence so far is limited. A preliminary prototype shows two dated satellite images of one area in a common 2D frame and a change layer for inspection. It does not show damage grades, people, hazards or routes, and no accuracy or speed has been measured. The report therefore establishes what RescueVision is designed to do and how it is designed to do it; it does not yet show that the platform works or that it improves a response.

## FUTURE WORK

Project II is planned to turn the design into a working platform and to test it. The planned work is:

**Train and evaluate the models.** Train the damage, building, flood and person-detection models on xBD, FloodNet, RescueNet and SARD, and report per-class results on held-out disaster events using the metrics set in Section 3.2.4. Compare the configured EfficientNet-B3 classifier with one agreed DINO backbone on the same building crops.

**Compute real routes.** Load a road network from OpenStreetMap or Overture, compute vehicle-specific routes with closures and flood depths, and measure how often a blocked road is wrongly marked safe.

**Build the 3D view.** Produce 3D tiles from drone imagery with OpenDroneMap and measure their position error against ground control points.

**Track people and manage cases.** Link detections into tracks, convert confirmed tracks into assistance cases and connect verified citizen requests to the same case list.

**Implement compound hazard rules.** Implement the Electrified Water rule with its road closures and re-planning, and confirm the rule distances with civil-defence or utility advice.

**Field application and user testing.** Complete the mobile field application with offline storage and SOS, and run a task-based evaluation of the console and the mobile application with emergency-service users or a tabletop exercise.
