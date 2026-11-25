# Red-team architecture review — RescueVision (Architect D)

**Date:** 25 November 2026 · **Author:** Red-team Architect D (GLM-5.4, max reasoning) · **Role:** second-opinion architect, arguing against the current plans

**Reviewed:** 57 of the 58 Markdown files in the repository in full (including `AGENTS.md`, `docs/**`, `docs/architecture/**`, `docs/documentation/chapter5/section_3_3.md` and every README); of the fifty-eighth, the generated `appendix_data_dictionary.md`, the header only, because I read the schema SQL it is derived from. Also reviewed: the Python, SQL, YAML, Docker and notebook files at `main` (`c947db4`), and the unmerged branch `codex/building-damage-v4`.

## How to read the evidence in this report

Every finding says how it was checked. There are four kinds of evidence and they are not equal:

| Tag | Meaning |
|---|---|
| **read** | I read the file at the stated line in this repository. |
| **ran** | I ran a read-only command (git, grep, a JSON parse of notebooks, the GitHub API) and saw the output. |
| **static** | A conclusion derived by reading SQL. **Not executed.** The local PostgreSQL server asks for a password I do not have, and I was told to write nothing outside this file, so I created no database. Each such finding comes with a test the team can run. |
| **search** | A fact taken from an official document or a web search in this session. The URL is in Sources. |

No repository file was edited, nothing was installed, nothing was committed. I did not read `redteam_gemini.md`, `glm_proposal.md` or `ai_specialist_gemini.md`; the reviews are meant to be independent.

**Architect A's proposal changed while this review was being written.** `gemini_proposal.md` grew from 411 to 430 lines at 19:24 and gained a folder of 14 companion documents. Every reference to it here is to the 430-line version. I did not read the companion documents; where I say the proposal lacks something, I also searched those files for the keyword and say so.

Severity: **Critical** = blocks the flagship demonstration or makes a safety or accuracy claim in the report untrue. **Major** = will cause rework, or weakens a claim an examiner will ask about. **Minor** = hygiene.

---

## Executive summary

1. **The plans describe a platform the repository does not contain.** On `main` there is no working backend, no ML package and no frontend code. The built assets are a 2,911-line PostgreSQL schema (genuinely good) and 27 Kaggle notebooks that are all broken at import today.
2. **Both architecture proposals were written against the documentation, not the code.** Neither mentions that commit `f89a61f` deleted `src/` and `tests/`, that 13 Python files at `main` make 56 imports of the deleted package, that all 27 notebooks are broken at import, or that the real ML work sits on an unmerged branch. Architect A's late revision calls the empty `src/` "expected" and moves on.
3. **The flagship safety loop has two defects in the SQL (static, not executed).** A Field Responder cannot trigger the hazard engine under row-level security, which is exactly the report's own UC-07 flow; and closures resolved in one order leave roads closed permanently.
4. **Re-routing does not exist.** The engine only marks routes `INVALIDATED`; nothing computes a replacement and the schema has no column to link one.
5. **Both proposals build on MinIO**, whose repository now begins "THIS REPOSITORY IS NO LONGER MAINTAINED". Replace it with a maintained S3-compatible store (RustFS or SeaweedFS, both Apache-2.0).
6. **Both propose a GPU-dependent AI topology although the team has no GPU.** The only compute is free Kaggle T4s, where the team's own log records the 7B-teacher profile as `BLOCKED_INSUFFICIENT_MEMORY`. Design CPU-first.
7. **F3 (person detection) and F4 (tracking), the most distinctive claims, are at zero**: no code, no notebook, no dataset. The seed registry nevertheless marks both models `is_active` `true`.
8. **No trained-model result is committed.** All 34 notebooks have zero saved outputs and `docs/experiments.md` lists 11 of 11 experiments "Pending". The only numbers live on an unmerged branch, use an approximate metric (0.6463), and the team's own V4 plan records that an earlier notebook chose its settings on the test split.
9. **The platform plan's core-backend choice (NestJS) contradicts the frontend's own design**, which generates its types from FastAPI's `/openapi.json`, and would split six students across two backend languages. Keep one language: Python.
10. **Headline proposal: a safety-first "incident twin".** An append-only incident event log becomes the single spine: durable outbox, resumable live updates, offline sync, replay and regression tests. Hazard evaluation becomes a database trigger, and routability is *derived* from active alerts instead of being mutated and restored.
11. **That spine removes Redis, LitServe and (for live layers) Martin** from the architecture: about six containers in the core profile plus three AI containers, against 9 in the platform plan and 14 or more in Architect A's proposal.
12. **AI as replaceable "observers"**: one serving template, three model-family containers, a registry that refuses to activate a model without a weights hash and evaluation evidence, and calibrated confidence (conformal prediction) feeding a prioritised human-review queue.
13. **Plan for 3 to 4 effective builders, not 6.** The 26 non-merge commits on `main` come from four people, 23 of them from two. Scope: one incident end to end, one or two real models, and an explicit cut list (Gazebo/ROS, 3D Gaussian splatting, Kubernetes, Kafka, CRDT documents, WebGPU shaders).
14. **The report and plans need 47 corrections (Section 5), on top of 12 critical and 46 major findings.** The minimum: the reversibility claim (§3.3.8.2), the audit-log claim (§3.3.3.5), the 60-second field-report claim (UC-07), the "can be retried" claim (UC-02), and a dozen stale documents.
15. **Do first, in this order:** fix the responder-to-engine path and the closure-restore logic with regression tests; restore one working codebase; replace MinIO; write six decision records; then build the event log and the offline sync protocol that the ERD specification explicitly left undesigned.

---

## 1. Diagnosis

### 1.1 What is actually in the repository

| Area | What the documents say | What is there | Evidence |
|---|---|---|---|
| Database | 56 tables, 8 domains, RLS, hazard engine | **Real.** 2,911 lines of schema, seed and self-check SQL; 313 of them tests | read, `database/schema/*.sql`, `database/tests/checks.sql` |
| ML package | `README.md:94` documents `src/rescuevision/` with data, models, training, inference, reporting | **Deleted.** 0 files under `src/` or `tests/` at `main` | ran: `git ls-tree -r HEAD` returns 0; `3c699f7` had 59 |
| ML training | "Use the notebooks in `notebooks/` on Kaggle" (`README.md:66`) | 34 notebooks, **0 saved outputs**; 27 of them import the deleted package from an unpinned clone | ran: JSON parse of all notebooks |
| Backend API | `docs/api_usage.md` documents 7 endpoints | **Broken at import.** 178-line FastAPI prototype importing the deleted package | read, `api/services/inference_service.py:12` |
| Frontend (new) | `frontend/README.md` describes a Turborepo with web, mobile and four packages | **23 README files and 6 config files. 0 lines of code.** No `package.json` in any app or package | ran: `find frontend -type f` |
| Frontend (legacy) | `docs/PROJECT_ANALYSIS.md:54` "React + TypeScript frontend (~560 lines)" | 8 TSX files; dependencies are `axios`, `react`, `react-dom` only; no map library | read, `dashboard/package.json` |
| Mapping prototype | 2D before/after map | **Real** (Folium/Leaflet HTML output); change overlay is a pixel baseline | read, `mapping/README.md` |
| Deployment | "Docker-ready" | `Dockerfile` and a 30-line Compose file with 2 services; no database, no object store | read, `docker-compose.yml` |
| CI | — | None (no `.github`, no other CI config) | ran |
| Tests | "Unit tests" (`README.md:102`) | 4 API smoke tests whose import fails; `checks.sql` on the database side is solid | read, `api/tests/test_api_smoke.py` |
| ML research (unmerged) | Not mentioned in any document on `main` | `codex/building-damage-v4`: 12 commits, 62 files, 14 test modules, its own experiment registry | ran: `git log main..codex/building-damage-v4` |

The single most important sentence for the team is in the unmerged branch, not on `main`: *"The V4 namespace is intentionally separate from the removed legacy package imports used by the API and old scripts. No API predictor was replaced or silently repaired."* (`codex/building-damage-v4:docs/v4_experiments.md`). Someone knows the API is dead. `README.md` still shows a Quick Start that cannot run.

### 1.2 Critical findings

#### C1 · Critical · There is no working backend or ML code on `main`

- **Evidence (ran):** commit `f89a61f` (21 October 2026), "Refactor: Remove segmentation training script and associated utility functions", changed 119 files with 6,539 deletions. `api/services/*.py` (3 files) and 10 files in `scripts/` contain 56 `from rescuevision…` / `import rescuevision…` statements. `python3 -c "import rescuevision"` with `src` on the path gives `ModuleNotFoundError`.
- **Also read:** `scripts/setup_env.sh:32` now says `[ -d src ] && pip install -e . || echo "note: no src/ package yet, skipping editable install"`. `requirements.txt` lists no `fastapi`, `uvicorn` or `python-multipart` (grep over `requirements.txt`, `pyproject.toml`, `dashboard/package.json` returns nothing), so the image built by `Dockerfile:14` cannot run its own `CMD ["uvicorn", "api.main:app", …]`.
- **Consequence:** `README.md`, `docs/api_usage.md`, `docs/model_cards.md`, `docs/dataset_setup.md` and `docs/PROJECT_ANALYSIS.md` (line 372: *"This is a complete product, not a prototype or notebook"*) describe software that is not in the repository. An examiner who clones the repo finds a database and notebooks.
- **Fix:** Phase 0 of the roadmap (Section 4). Recover the package from `3c699f7` into one installable package, merge or retire V4, and rewrite or mark the stale documents as historical.

#### C2 · Critical · All 27 Kaggle notebooks are irreproducible, and are broken today

- **Evidence (ran):** each of the 27 notebooks in `notebooks/kaggle/` runs `git clone -q https://github.com/AliOmarAbdelhady/RescueVision.git` with **no branch or commit pinned**, then `sys.path.insert(0, str(REPO / "src"))` and imports one or more of 20 distinct `rescuevision.*` modules (for example `rescuevision.training.train_segmentation`, `rescuevision.data.xbd_parser`, `rescuevision.models.unet`). The origin default branch is `main`, which has 0 files under `src/rescuevision/`. No notebook writes those modules itself. Dependencies are installed with `pip install --upgrade` on lower bounds such as `torch>=2.1.0`.
- **The team already knows.** The V4 plan lists as problem 7: *"Dependencies and source are unstable. The setup cells clone an unpinned repository revision; some installs use `check=False`; code is duplicated and monkey-patched inside notebooks."* (`codex/building-damage-v4:docs/building_damage_v4_research_plan.md`).
- **Consequence:** no past number can be regenerated; a fresh run fails at the first import. Any accuracy figure in the final report would rest on runs nobody can repeat.
- **Fix:** notebooks become thin wrappers over a versioned wheel (`pip install rescuevision==<version>` from a build produced in CI), with the git commit, package version and dataset digests written into every run manifest. V4 already works this way (`notebooks/kaggle/v4/`); make it the rule.

#### C3 · Critical · F3 and F4 are at zero, but the registry says the models are active

- **Evidence (ran):** a case-insensitive search for `yolo`, `bytetrack`, `sard`, `visdrone` across all 34 notebooks returns no file. `docs/experiments.md` has no experiment for person detection.
- **Evidence (read):** `database/seed/01_reference_data.sql:117-118` inserts `('person-detector', '1.0.0', 'PERSON_DETECTION', 'YOLOv8s', ARRAY['SARD','VisDrone','POP'], true)` and `('person-tracker', …, 'ByteTrack', ARRAY[]::text[], true)`. `metrics` and `weights_uri` are absent. Nine models are seeded this way, all `is_active = true`, none with metrics.
- **Consequence:** `ai_models` is the provenance anchor for FR-IM-07 ("every result names the model version"). A registry that marks untrained models active defeats the purpose on day one. The ERD specification also promises detection when *"only part of the body is visible: half-covered by debris, behind walls, or only head or limbs exposed"* (`docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md:18`); nothing exists to support that sentence.
- **Fix:** Section 3.5 (registry gate). In the report, F3 and F4 stay "proposed" until there is a trained, evaluated model.

#### C4 · Critical · A Field Responder cannot trigger the hazard engine (static)

This is the report's flagship use case, and by the policies it fails.

- **The engine runs with the caller's rights.** `database/schema/15_security.sql:241-242`: *"The hazard engine stays SECURITY INVOKER on purpose: it runs with the caller's rights, so only users allowed to write alerts/roads can fire it."*
- **What the engine writes needs other permissions.** `evaluate_hazard_rules` inserts into `compound_alerts`. The policy for that table (`15_security.sql:598-602`) requires `analysis.run` **or** `alert.resolve`. The update of `road_segments` (`:513-517`), the insert into `alert_closed_segments` (`:610-612`) and the insert into `notifications` (`:659-662`, requires `mission.assign`, `analysis.run` or `alert.resolve`) need the same.
- **The responder has none of them.** `database/seed/01_reference_data.sql:59-62`: `FIELD_RESPONDER` holds `incident.view`, `mission.update_status`, `case.update`, `case.triage`, `hazard.report`, `sos.raise`, `position.share`. A Commander has `alert.resolve` but **not** `hazard.report` (`:48-52`), so a commander cannot report a hazard either. The only role that can both report a hazard and fire the engine in one transaction is the Analyst, at a desk.
- **The prescribed flow is the failing one.** `docs/documentation/chapter5/section_3_3.md:301`: *"A single flood report from the field leads, within the 60-second target of NFR-PF-04, to a danger zone, closed roads, invalidated routes and warnings"*. Architect A's flow 4.4 step 2 states it as code: *"Calls `SELECT evaluate_hazard_rules($incident_id)` … in the same transaction"*.
- **What happens (static):** the responder's hazard insert passes RLS. The engine then hits `INSERT INTO compound_alerts`, fails the `WITH CHECK` of `compound_alerts_engine` with SQLSTATE `42501`, and the whole transaction aborts, **including the flood report**. If the API instead calls the engine in a second transaction under another role, the alert is no longer atomic with the report.
- **Nothing tests it.** `database/tests/checks.sql:307-308` runs the engine only as `analyst@gov.demo`. In the demo the Electrified Water alert comes from an AI-detected flood inserted by the owner (`database/seed/02_demo_scenario.sql:294-298`), and the engine is then called by the owner (`:321`), who bypasses RLS.
- **Test to add** (I expect it to fail today):

```sql
BEGIN;
SELECT app.set_session_user((SELECT id FROM users WHERE email = 'para1@ems.demo'));  -- FIELD_RESPONDER
SET LOCAL ROLE rv_app;
INSERT INTO hazards (incident_id, hazard_type, geom, severity, origin, reported_by)
SELECT h.incident_id, 'FLOOD_WATER', ST_Translate(h.geom, 0.0002, 0), 4,
       'RESPONDER_REPORTED', app.current_user_id()
FROM hazards h WHERE h.hazard_type = 'FLOOD_WATER' LIMIT 1;
SELECT evaluate_hazard_rules((SELECT id FROM incidents WHERE code = 'INC-2026-0001'));
-- expected by reading the policies: ERROR 42501, new row violates row-level security
-- policy for table "compound_alerts"
ROLLBACK;
```

- **Fix:** Section 3.4. Make the engine `SECURITY DEFINER` with a fixed `search_path` and call it from a trigger on `hazards` and `infrastructure_assets`. The right to insert a hazard then *is* the right to trigger evaluation, and the effect is atomic with the report.

#### C5 · Critical · Road closure restore is order-dependent and can leave roads closed forever (static)

- **Evidence (read):** when an alert closes roads, the engine snapshots the segment's *current* state whatever it is (`database/schema/12_hazard_engine.sql:108-112`):

```sql
INSERT INTO alert_closed_segments (alert_id, segment_id, prev_condition, prev_cost, prev_reverse_cost)
SELECT v_alert, s.id, s.condition, s.cost, s.reverse_cost
FROM road_segments s
WHERE s.incident_id = p_incident AND ST_Intersects(s.geom, v_zone)
ON CONFLICT DO NOTHING;
```

  `ON CONFLICT` guards only the same alert. `resolve_compound_alert` restores `prev_*` unless another live alert covers the segment (`:167-175`).
- **Trace (static):** flood report A and flood report B both lie within 30 m of the same transformer and share road segment S. Alert A1 closes S and stores `prev = CLEAR, 10, 10`. Alert A2 also closes S and stores `prev = HAZARD_CLOSED, -1, -1`. Resolve A1 first: S is skipped because A2 is live. Resolve A2: S is restored to `HAZARD_CLOSED, -1, -1`. **The road is now closed with no active alert.** Resolve in the other order and it works, so the bug depends on which alert a commander clicks first.
- **It cannot repair itself.** `database/schema/07_roads.sql:73` lets a new observation update the cached condition only `AND condition <> 'HAZARD_CLOSED'`. A responder reporting "road is clear" cannot reopen it.
- **A second defect, same code.** While a segment is closed, observations are ignored (`07_roads.sql:71-73`). If the road becomes blocked by debris during the closure, resolving the alert restores `CLEAR` and the map shows a blocked road as open.
- **The report claims the opposite.** `section_3_3.md:337`: *"Third, it is reversible: each closed segment keeps its previous condition and costs, and resolving the alert restores them unless another active alert also covers the segment."* The only test (`checks.sql:96-108`) covers one alert, re-run idempotency, and one resolve.
- **Fix:** Section 3.4, "derive, do not restore". Do not mutate road costs. Compute routability at query time from live alerts and the latest observation.

#### C6 · Critical · "Recomputes routes" was never built

- **Evidence (read):** `12_hazard_engine.sql:119-126` only does `UPDATE routes rt SET status = 'INVALIDATED', invalidated_by_alert_id = v_alert`. `routes` (`database/schema/10_routing.sql:4-25`) has no column for a successor route. `checks.sql:137-147` computes a detour with `pgr_dijkstra` but never stores it.
- **The documents promise it:** ERD specification line 27, *"invalidates and recomputes routes passing through the zone"*; the project brief, *"closing roads and re-routing rescuers"*. Architect A's flow 2 step 3 says the API *"immediately computes safe replacement routes"*; no code or schema exists for it.
- **Consequence:** today a team whose route is cut receives a warning and nothing else. That is the weakest possible version of the flagship feature.
- **Fix:** Section 3.4, step 5. Add `supersedes_route_id`; an event consumer computes the replacement and emits `route.replaced` or `route.no_safe_route`.

#### C7 · Critical · The job table cannot carry the queue semantics the design relies on

- **Evidence (read):** `processing_jobs` (`database/schema/04_imagery_ai.sql:66-78`) has `id, incident_id, session_id, job_type, status, progress_pct, error_message, requested_by, queued_at, started_at, finished_at`. `job_type` is `STITCH | ANALYZE | ROUTE | REPORT` and `job_status` is `QUEUED | RUNNING | SUCCEEDED | FAILED` (`01_types.sql:33-34`). There is no attempt counter, retry limit, lease or heartbeat, priority, dependency between jobs, cancellation or dead-letter state.
- **The report relies on them.** D-03 (`section_3_3.md:64`): jobs *"can be retried"*; §3.3.6 (`:305`): *"a failed job shows its error and can be retried"*. Both proposals make this table the durable queue with `FOR UPDATE SKIP LOCKED`.
- **Consequence (by construction):** a worker that dies mid-stitch leaves the row `RUNNING` forever; nothing chains STITCH before ANALYZE, although ANALYZE needs the orthomosaic; an SOS-related analysis queues behind a routine report.
- **Fix:** Section 3.3. Keep `processing_jobs` as the record the user sees; let a queue library own leasing and retries; add a `job_steps` table for resume.

#### C8 · Critical · The worker role can rewrite or delete the audit trail

- **Evidence (read):** `15_security.sql:259` grants `SELECT, INSERT, UPDATE, DELETE ON ALL TABLES … TO rv_app, rv_worker`. The loop at `:299-312` then creates on **every** table, `audit_log` included, `CREATE POLICY service_all … FOR ALL TO rv_worker USING (true) WITH CHECK (true)`. `audit_log` is not itself audited (the trigger list at `:218-224` does not include it).
- **The report claims otherwise.** `section_3_3.md:196`: *"no application role can modify the log (NFR-SC-06)"*. Table 3-43 lists `rv_worker` as one of the four roles applications connect through.
- **Consequence:** the AI pipeline is a role with full access to every row, including citizens' phone numbers and session hashes, and it can alter the record of its own actions. A single compromised or prompt-injected AI container defeats the audit requirement.
- **Fix:** revoke `UPDATE, DELETE` on `audit_log` from every login role except a migration role; give the worker INSERT-only, incident-scoped grants on the tables it writes.

#### C9 · Critical · Both proposals rest on an unmaintained object store and a GPU that does not exist

- **MinIO.** `docs/architecture/platform-architecture-plan.md:70` lists `storage | MinIO`; `gemini_proposal.md:277` lists `minio | MinIO (S3 API) | … model weights`. The repository's README now opens (search, `https://github.com/minio/minio`): *"**THIS REPOSITORY IS NO LONGER MAINTAINED.**"* and *"the MinIO community edition is now distributed as source code only. We will no longer provide pre-compiled binary releases for the community version."* The GitHub API shows it archived, last push 2026-04-24, licence AGPL-3.0. The successor, AIStor, is a licensed product. Decision D-09 promises *"No licence cost for public agencies"*.
- **GPU.** The platform plan scales its AI services "by GPU" and the report says *"workers with graphics processors take jobs from the queue"* (`section_3_3.md:42`). The V4 ledger states *"the laptop is source-only"* and *"No paid/multi-GPU allocation was supplied"*; its gate K5 is `BLOCKED_INSUFFICIENT_MEMORY` on a Tesla T4; `nvidia-smi` is absent on this machine. Neither proposal says where a GPU for development, load testing or the live demonstration comes from. Architect A hand-waves it: *"Ephemeral Burst GPU Nodes (e.g., RunPod/AWS/GCP L4 or A10G VMs)"* (`gemini_proposal.md:350`).
- **Consequence:** the architecture fails on its two most concrete dependencies. A demonstration that needs four CUDA containers and an archived object store will not start on a student laptop.
- **Fix:** Section 3.2 (object store) and Section 3.5 (CPU-first inference, with a rented GPU only for final load testing).

#### C10 · Critical · Model evaluation has holes and no result is committed

- **Evidence (read, unmerged branch):** `codex/building-damage-v4:docs/building_damage_v4_research_plan.md` records a saved subset result of *"373 test tiles; pixel localization IoU 0.7108; pixel damage macro-F1 0.6986; `xview2_approx.overall_f1` 0.6463"*, with per-class damage F1 of intact 0.9508, minor 0.5086, major 0.4585, destroyed 0.8765. The same file lists nine material problems, including *"RV3 rescore selects settings on test data"* (cell 11 sets `SCORING_SPLIT = "test"` and picks `best_key`) and *"Checkpoint selection optimizes the wrong proxy"* (`0.5 * loc_iou + 0.5 * damage_macro_f1`).
- **The official metric is different.** `DIUx-xView/xView2_scoring/xview2_metrics.py:255` (ran) computes `0.3 * self.lf1 + 0.7 * self.df1`, with `df1` the harmonic mean of the four damage F1 scores. The notebooks' `xview2_approx` is a connected-component approximation written by the team.
- **On `main`:** all 11 experiments are "Pending" (`docs/experiments.md:5-15`); the notebooks commit no outputs; `outputs/` is absent from this checkout.
- **Targets disagree.** `docs/claude_view.md:213` says the correct figure is about 0.74; the V4 plan sets *"official xView2 combined F1 above 0.82"* as a milestone and warns that 0.74 *"must not be presented as a universal ceiling"*. I did not verify either number against the leaderboard.
- **Consequence:** the numbers that exist are optimistically biased by test-set selection, measured with a home-made metric, and live only on a branch. This is the first thing an examiner will probe.
- **Fix:** Section 3.5. Score with the official scorer, freeze the test split, select on validation only, and commit an `evaluations/` table of record to `main`.

#### C11 · Critical · F3's distinctive labels have no labelled data behind them

- **Evidence (read):** `person_detections` requires `visibility visibility_level NOT NULL` (`FULL | PARTIAL | HEAD_ONLY | LIMBS_ONLY`), `occlusion_ratio` and `posture` (`database/schema/08_persons_cases.sql:35-37`). These are stored as if they were observed facts.
- **No public dataset labels them (search, counts unverified):** SARD is reported as 1,981 images of people in terrain, HERIDAL as roughly 1,700 high-resolution images in European landscapes, SeaDronesSee as about 5,630 images with classes `swimmer, floater, boat, jetski, buoy, life-saving appliances`. All three label boxes only, and none is an urban flood or collapse scene in Egypt.
- **Consequence:** the detector can emit a box and a confidence. Visibility, occlusion ratio and posture would be guesses stored in non-null columns, then shown to an Analyst as attributes (Table 3-46: "Image crop with box, confidence, visibility, occlusion, posture"). That is a false impression of evidence.
- **Fix:** make these columns nullable, add a `attribute_source` (`model | annotator | heuristic`) and a confidence for each, and build a small team-annotated evaluation set (500 images stratified by visibility) before claiming partial-visibility detection.

#### C12 · Critical · The planning documents contradict each other on the basics

| Topic | One document says | Another says |
|---|---|---|
| Core backend | "`core-api (NestJS)`" — `platform-architecture-plan.md:13` | Types are "**generated from FastAPI's `/openapi.json`**" — `frontend/packages/api/README.md:28`; FastAPI core in `gemini_proposal.md:13` |
| Simulation | "6. **Gazebo/PX4 simulation demo**" is one of six scope items, with its own Phase 7 — `docs/graduation_project_research_plan.md:312,465` | Absent from `section_3_3.md` and from both architecture proposals |
| Drone | "a real DJI drone + GPU compute" — `docs/claude_view.md:15` | "No real drone, no dataset, no ready simulator" — `docs/SAR_Drone_Simulation_Research.md:7` |
| PostgreSQL | "Target: PostgreSQL 16" in a header that also says "implemented … (PostgreSQL 18.7)" — ERD specification line 3 | PostgreSQL 18 in the review vocabulary and Person 5's plan |
| RLS | "enforced in the API layer, with **optional** Postgres Row-Level Security" — ERD specification line 83 | D-04: RLS **is** the enforcement point — `section_3_3.md:65` |
| Product state | "a complete product" — `docs/PROJECT_ANALYSIS.md:372` | "a **research prototype**" — `README.md:119` |
| Modules | Figure 3-3 caption: "nine domain modules"; line 40 lists ten | "grouped into eight domains … the domain names match the modules of Figure 3-3" — `section_3_3.md:108` |
| Flood imagery | "UAV imagery from Hurricane Florence" — `docs/PROJECT_ANALYSIS.md:238` | "captured after the hurricane Harvey" — arXiv 2012.02951 (fetched) |

- **Consequence:** the report is assembled from these documents. Each row is a question an examiner can ask.
- **Fix:** Section 5.

### 1.3 Major findings

#### Architecture and the two proposals

| ID | Where | Finding | Consequence |
|---|---|---|---|
| P1 | `platform-architecture-plan.md:3` "Nothing here is built yet"; `:16` "(already built in `database/`)"; `gemini_proposal.md:32` "empty `src/` or scaffolded `frontend/` folders are expected" | Neither proposal assesses what exists. The platform plan's repository layout (`backend/core-api`, `backend/services`) ignores `api/`, `scripts/`, `configs/`, `notebooks/` and the V4 branch. Architect A's late paragraph notices the empty folders and treats them as a starting point, not as broken software. | Nobody can start work from either without rediscovering Section 1.1 first. |
| P2 | `platform-architecture-plan.md:13` "**NestJS** (TypeScript) modular monolith"; `gemini_proposal.md:13` FastAPI | The two proposals disagree on the core, and the NestJS choice breaks the team's own contract: `frontend/tooling/README.md:5` and `frontend/packages/api/README.md:28` generate all client types from FastAPI's `/openapi.json`. | Two backend languages for six students, or a rewrite of the frontend design. See Section 3.1 for the decision. |
| P3 | `platform-architecture-plan.md:83-85`; `gemini_proposal.md:14,155` | `LISTEN/NOTIFY` is treated as the event transport. It is a wake-up hint, not a queue: the payload must be under 8,000 bytes, delivery happens only at commit (PostgreSQL docs, fetched), and a notification sent while no listener is attached is not kept for later (PostgreSQL docs on `LISTEN`; not re-fetched). There is no outbox. | An alert committed while the relay restarts is never pushed. NFR-PF-04 (60 seconds) cannot be demonstrated. |
| P4 | `gemini_proposal.md:14,224,278` | Redis is added for three things: WebSocket fan-out across API replicas, GPS throttling and OTP limits. | None needs Redis at pilot scale (one or two API processes), Redis Pub/Sub is itself fire-and-forget, and it is one more stateful service to back up and secure. Remove. |
| P5 | `gemini_proposal.md:96` "Do NOT use raw FastAPI … Use `LitServe`" | LitServe's latest release is v0.2.19 (2026-09-09), pre-1.0, and its README now leads with "Agents, RAG, pipelines" (ran). Its selling point, dynamic batching across concurrent requests, solves a problem this system does not have: one worker tiles each orthomosaic and can send batches itself. | A dependency on a moving 0.x framework for no measurable gain. |
| P6 | Both proposals; `gemini_proposal.md:368-395` | Neither main document has a time-phased roadmap, a risk register or a scope cut, and a keyword search of Architect A's 14 companion documents finds none. Architect A's inventory is 14 core containers plus Prometheus, Grafana and an OTel collector. Its revision adds useful things (a hosting topology, CI/CD, a training-workspace layout, a repository clean-up plan), but the GPU is still an assumed "burst GPU node" and the object store is still MinIO. | The plan is not executable by the team that must execute it. |
| P7 | `gemini_proposal.md:85,106,122,185` | Unchecked evidence: BentoML "~13k★" (API: 8,950); NodeODM said to return "3D Mesh Tiles" (not in ODM's README); `pmtiles://file://…` asserted for MapLibre React Native (no PMTiles file in that repo's tree); `OCHA-DAP/ds-geospatial-impact-estimates` cited as a humanitarian platform (1 star, no licence). | Individually small; together they mean the research was not verified. Check every number before any of it enters the report. |
| P8 | `gemini_proposal.md:298-300` | Flow 2 prescribes the engine call in the responder's own transaction, which is the path that fails (C4). | The detailed design repeats the defect. |

Minor: the "15 to 20 engineers" rule of thumb (`platform-architecture-plan.md:20`) comes from blog posts; most sources at lines 159-173 are vendor blogs. "TorchServe … Repository archived" (`:99`) is correct (API: archived, last push 2025-08-06).

#### Database, RLS and the hazard engine

| ID | Where | Finding | Consequence |
|---|---|---|---|
| D1 | `database/build.sh:20` `DROP DATABASE IF EXISTS … WITH (FORCE)`; no migration directory; `15_security.sql` uses plain `CREATE POLICY` | The only way to change the schema is to destroy the database. | Every schema change loses data, including the audit trail the report promises. |
| D2 | `12_hazard_engine.sql` (whole file) | The engine is only ever called explicitly (ran: references exist in the seed, the tests and one `GRANT`; there is no trigger). | A writer that forgets to call it leaves an unevaluated hazard. Safety should not depend on remembering. |
| D3 | `12_hazard_engine.sql:27-31` | Idempotency is checked per *hazard*. A second flood report near the same transformer opens a second alert for the same asset. | One asset, several banners; and it is the trigger for C5. |
| D4 | `15_security.sql:584-586,521-524` | The app role can insert hazards only with `origin = 'RESPONDER_REPORTED'` and road observations only with `reported_by` set, while CHECK constraints allow exactly one source. No function turns a verified citizen request into a hazard. | A citizen's flood report (FR-FC-07, type `HAZARD`) can never reach the rule engine through the application role. |
| D5 | `12_hazard_engine.sql:41` `AND a.power_state <> 'DE_ENERGIZED'` | The electrical test is applied to every asset type, including `GAS_PIPELINE` and `FUEL_STATION` (rules `FIRE_NEAR_FUEL`). | A fuel station marked `DE_ENERGIZED` silently switches off the explosion rule. |
| D6 | `seed/01_reference_data.sql:68-71`; `section_3_3.md:337` | `ELECTRIFIED_WATER` fires for any line, transformer or substation within 30 m, buffered 25 m. The report admits the values are unconfirmed. Electrical safety guidance is about contact: the ground up to 35 feet (about 10.7 m) from a *downed* line may be energised (search, ESFI). | An intact overhead line above water is treated like a downed one, and a ground-mounted transformer in 40 cm of water is treated the same as one on a dry embankment. The rule is both over- and under-inclusive. |
| D7 | `12_hazard_engine.sql:136` `ST_DWithin(…, 0)` | Only responders whose last position lies inside the zone are warned. "Near" (FR-HZ-09) is not implemented; responders with no position row or with a mission targeting the zone get nothing. | The people most likely to drive into the zone are not told. |
| D8 | `07_roads.sql:8,16` `incident_id … NOT NULL` | Roads (and in the specification, buildings) are copied per incident, and a road condition belongs to the segment, not to (segment, incident). | Two overlapping incidents must duplicate the network and overwrite each other's conditions. Tolerable for a one-incident pilot; say so, or split a shared base layer from per-incident observations. |
| D9 | `04_imagery_ai.sql:102`; `08_persons_cases.sql:9-10,18,28` | Every inference run must consume a raster product; a track is bound to one run (`UNIQUE (inference_run_id, tracker_local_id)`). | Per-frame detection before an orthomosaic exists is impossible, and a track cannot survive a second sortie. The schema enforces batch-only analysis. |
| D10 | `04_imagery_ai.sql:57-59`; `11_field_reports_audit.sql:126` | `metrics` is nullable and `is_active` is unconstrained; `embedding vector(768)` fixes the dimension while V4 profiles ViT-L. | The registry cannot enforce provenance (C3); an embedding-model change is a migration. |

Minor: more than 40 ENUM types (`01_types.sql`) mean a new hazard or request type is a migration, so "rules as data" (D-05) stops at the enum; "AI / Celery pipeline" in `database/README.md:69` and `15_security.sql:7` while both proposals use a Postgres queue; two ERD generators and two diagrams of one schema (10 pages in `docs/database`, 11 in `mahmoudERD/`, "8 domains" against "9 subject areas"); `checks.sql` has no test for overlapping alerts resolved in both orders, the responder path, an observation made during a closure, or the worker role against `audit_log`.

#### AI

| ID | Where | Finding | Consequence |
|---|---|---|---|
| A1 | `codex/building-damage-v4:docs/v4_experiments.md` gate K5; V4 plan "No paid/multi-GPU allocation was supplied" | The compute budget is free Kaggle T4s; the 7B teacher profile is blocked for memory. | A distillation programme designed around a 7B teacher cannot run on the available hardware. Drop the 7B teacher; profile ViT-L first. |
| A2 | `configs/dinov2_damage_classifier.yaml:15`; `seed/01_reference_data.sql:115,122`; `docs/research_papers.md:14` | Three generations coexist: configs and registry use DINOv2, the paper list cites DINOv3, V4 trains DINOv3 ViT-L on SAT-493M. The person model is `YOLOv8s`; Ultralytics' current line is YOLO26 (README, ran). | The report cannot state one model per task until this is settled. |
| A3 | `pyproject.toml:11` (MIT); Ultralytics README line 33; API licences | `ultralytics/ultralytics` is AGPL-3.0 ("Request an Enterprise License for commercial use"); OpenDroneMap and NodeODM are AGPL-3.0; Grafana is AGPL-3.0. | D-09 promises an open stack with no licence cost for public agencies. AGPL is not "no cost" for a distributed government deployment; it is a legal decision the team has not taken. Apache-2.0 detectors exist: RT-DETR, RF-DETR, YOLOX, D-FINE (ran). |
| A4 | `platform-architecture-plan.md:64`; `docs/claude_view.md:50` | One `ai-damage` service is listed for "building damage grades" with no sensor stated. xBD is satellite imagery; drone imagery is centimetre-level. | Models do not transfer across that gap; the service contract must say which sensor and ground resolution it serves. |
| A5 | `section_3_3.md:347-351`; `seed/01_reference_data.sql:93-96` | "AI restoration cost" is a deterministic formula with "placeholder local unit rates", and its dominant input (`floors`) is nullable. | Call it a cost model, not AI, and show sensitivity to the floor count. |
| A6 | ERD specification F4 (`:21`); FR-PT-04 | "A person who stays still for a long time may be injured." | Stationarity accumulates evidence for persistent false positives as well: a bag or a shadow is "stationary" for the whole flight. The rule promotes the most convincing mistakes. |
| A7 | `api/services/retrieval_service.py:18-19`; `frontend/apps/web/src/features/cases/README.md` | Two retrieval systems: FAISS in the old API, pgvector in the schema. | Keep pgvector, delete FAISS. FR-RP-10 is optional: cut it from the MVP. |
| A8 | `configs/inference.yaml:1` | `device: "cuda"` is the default and there is no CPU path. | Nothing runs on the machines the team owns. |

Minor: the POP dataset is thermal infrared (`docs/SAR_Drone_Simulation_Research.md:176-177`) but is listed beside RGB datasets for an RGB detector; TensorBoard logs only and no committed run record; four generations of ML plan (E1–E11, `rv`, `rv2`/`rv3`, V4) in one repository.

#### Frontend, mobile and maps

| ID | Where | Finding | Consequence |
|---|---|---|---|
| F1 | `frontend/packages/contracts/README.md:15-17`; both proposals "keep the existing `frontend/`" | The scaffold is 0 lines of code and models the old single-analyst tool: roles `COMMANDER / ANALYST / RESPONDER`, events `position, sos, job-progress, victim`, "cases" that are assessment outputs, "urgency" badges. | None of that is in the approved vocabulary or the schema. It is a sketch, not an asset. |
| F2 | `frontend/apps/mobile/src/features/tracking/README.md`, `…/emergency/README.md` | Positions and SOS are "published" over the WebSocket. The database makes tables with RLS the write path (`responder_positions_share`, `sos_alerts_raise`), and D-10 makes the live channel push-only. | WebSocket as a write path bypasses RLS, the audit trail and the offline queue. |
| F3 | `frontend/README.md:20-21` | Points to `docs/FRONTEND_ARCHITECTURE.md`, which does not exist (ran). | The "one rule" of the frontend has no document. |
| F4 | ERD specification line 404 | "Offline-sync conflict resolution … the protocol is a separate design." Neither proposal designs it. | The hardest part of D-08 is undesigned: operations accepted on a device and rejected at sync, danger zones that change while offline, routes invalidated while offline. |
| F5 | `frontend/apps/mobile/src/features/imagery/README.md` | The responder app uploads pre/post image pairs to `/predict`. | That is the Analyst's job in the approved design. |
| F6 | `gemini_proposal.md:185` | Offline maps on mobile are asserted, not shown. `maplibre/maplibre-react-native` (v11.5.1) has Expo setup docs and an Expo example, and no PMTiles or terrain module in its tree (ran). | A three-day spike must precede any commitment. |
| F7 | ERD specification line 15 "(CesiumJS, buildings extruded…)" | CesiumJS is Apache-2.0, but its ready-made terrain and building assets are served through Cesium ion under an access token (not re-verified this session). MapLibre GL JS (v6.19.0) has terrain in-tree and documents 3D Tiles through a three.js custom layer. | Two map engines for web and mobile, and a proprietary dependency that contradicts D-09. |
| F8 | `docs/claude_view.md:51` | "There is **no public dataset** of raw, overlapping, geotagged, photogrammetry-grade post-disaster drone imagery." | Orthomosaic, DSM and 3D depend on flying a drone whose existence the documents dispute (C12). |

Minor: IR-UI-07 requires Arabic and right-to-left layout; nobody has scheduled a test of Arabic label shaping on the map. Three frontends exist (`dashboard/`, `frontend/apps/web`, `mapping/output/*.html`).

#### Deployment, security, observability, testing

| ID | Where | Finding | Consequence |
|---|---|---|---|
| O1 | `api/main.py:41-47,54,62,79,85-89` | Legacy API: `allow_origins=["*"]` with `allow_credentials=True`; no authentication; `/outputs` mounted statically; whole uploads read into memory; blocking inference inside `async def`; deprecated `@app.on_event`; `enable_retrieval` accepted and ignored. | Must not be the starting point of the new core without a rewrite of every handler. |
| O2 | `docker-compose.yml:17`; `Dockerfile:1,31-44` | The healthcheck calls `curl`, which `python:3.11-slim` does not ship (verify once), so the service is always "unhealthy". Compose has two services and no database or object store. | The deployment files are a mock-up. |
| O3 | `.env.example`; `platform-architecture-plan.md:146` | No database URL, object-store credentials or signing keys; secrets are "environment variables or Docker secrets" with no rotation plan. | — |
| O4 | NFR-SC-01; `02_identity_access.sql` | Password hashing is an "adaptive hashing algorithm" with no name; no second factor for Commander or Admin; the citizen one-time code has no storage or attempt-limit table. | A multi-agency system with lives attached needs this specified. |
| O5 | `section_3_3.md:54`; NFR-RL-05 | Daily backup and a restore test are promised; no tool, no schedule, and nothing about consistency between database rows and the objects they reference. | A restore can produce rows that point at missing imagery. |
| O6 | Both proposals, observability paragraphs | Tools are named; no service level is defined for NFR-PF-04, NFR-PF-02 or NFR-RL-04, and no metric can show the 60-second alert target. | A target you cannot measure is a claim. |
| O7 | no CI configuration; `api/tests/test_api_smoke.py:14` | No CI; the only Python tests fail at `from api.main import app`. | `checks.sql` is the sole working test asset. |

Minor: `pyproject.toml:13` discovers packages under `src`, which is empty, so `pip install -e .` installs nothing (ran).

#### Team and documents

| ID | Where | Finding | Consequence |
|---|---|---|---|
| T1 | `git shortlog main`; `documentation-work-plan.md:21,438` | 26 non-merge commits in three months, from four people; two of them wrote 23. The team plan "assigns documentation work only" and "No development assignment is included." | Nobody is assigned to build the platform. Plan for 3 to 4 effective builders. |
| T2 | `README.md`, `docs/api_usage.md`, `docs/PROJECT_ANALYSIS.md`, `docs/model_cards.md`, `docs/experiments.md`, `docs/dataset_setup.md` | All describe the deleted package as the current system. | Mislead every new teammate and every AI assistant. |
| T3 | `docs/SAR_Drone_Simulation_Research.md:15,452,460`; `docs/graduation_project_research_plan.md:502` | One document makes AirSim the "TOP RECOMMENDATION", proposes a Streamlit dashboard and GPT-4o reports; the other says AirSim "is archived" (the API shows it is not: last release 2022, repository pushed 2026-09-15). | A research dump that contradicts every later decision. Mark as background. |
| T4 | `docs/claude_view.md:11,37-40` | "Git is broken (empty `.git/`)" is false; Gazebo simulation is a CORE item with a stated 3 to 6 week learning cost. | Simulation would consume the project. Cut it (Section 2.4). |
| T5 | `AGENTS.md` "Current focus" | Accurate about report ownership; silent on the facts in Section 1.1. | Each new session starts from the wrong picture. |

### 1.4 Verdict on the two proposals

| Question | Platform plan | Architect A (Gemini) | My verdict |
|---|---|---|---|
| Microservices? | No | No | **Both right.** |
| Where to split | AI, imagery, tiles | Same | **Both right.** |
| Core backend | NestJS | FastAPI | **Architect A right**; the platform plan contradicts the frontend contract (P2). |
| AI serving | Bare FastAPI | LitServe | **Platform plan right** (P5). |
| Queue | Postgres table + `LISTEN/NOTIFY` | Same, plus Procrastinate, plus Redis | **Both incomplete.** Neither has a durable outbox, a lease, retries or step resume (C7, P3, P4). |
| Object store | MinIO | MinIO | **Both wrong** (C9). |
| GPU | Assumed | Assumed; a revision adds a "burst GPU node" behind a rented server, with no budget or source | **Both unexamined** (C9). |
| Offline field app | Not designed | SQLite + PowerSync mentioned | **Both undesigned** (F4). |
| Roadmap, risks | None | None in the main document; a keyword search of the 14 companion documents finds no roadmap, risk register or week-by-week plan | **Missing** (P6). |
| Awareness of the repository | None | A late paragraph calls the empty `src/` and `frontend/` "expected"; silent on the 56 dead imports, the notebooks, V4 and MinIO's status | **Missing** (P1). |
| Citations | Blogs, one correct archive claim | Several unchecked numbers and an unshown capability | Re-verify before reuse (P7). |

### 1.5 What is good and must not be thrown away

- **The database.** Real integrity thinking: exactly-one-source `CHECK` constraints, partial unique indexes for "one current", typed foreign keys instead of polymorphic ids, `security_invoker` views, a column-guard trigger, partitioned append-only tables with defaults, UUIDv7 keys chosen because offline clients generate ids. `checks.sql` asserts behaviour, not structure. This is the best artefact in the project and should stay at the centre; my proposal changes a few functions and policies, not the model.
- **Decisions D-01, D-04, D-06 and D-07** (one shared incident, RLS, frozen snapshots, a person confirms). They are right and well argued.
- **The report's discipline.** Proposed behaviour is written as proposed; the review folder in `docs/team-plan/review/` is unusually honest and specific.
- **The V4 branch.** Strict artifact contracts, parity tests against the official scorer, checkpoint resume, thin notebooks. It is the most mature engineering in the repository. Merge it or make it the trunk.
- **Brand, mapping prototype and imagery credits.** A credible demonstration surface with honest limits.

---

## 2. Research

### 2.1 How the research was checked

- **GitHub API (ran, 25 November 2026).** About 130 repository lookups, of which about 100 distinct repositories were confirmed to exist; each was checked for archived flag, last push, latest release, licence and stars. Where I quote a star count, a release or "archived", it came from that call. "Licence: see repo" means the API returned no single recognised identifier.
- **READMEs (ran).** Feature claims about a library were taken from its own README, not from memory.
- **Official documents (search or fetched).** PostgreSQL `NOTIFY` page (fetched), PostgREST configuration page (fetched), FloodNet arXiv abstract (fetched), ESFI and NWS guidance (search), SeaDronesSee and SARD (search).
- **Where my memory was wrong, the API won.** Recorded here because the other proposals contain the same kind of error: `microsoft/AirSim` is **not** archived; `pytorch/serve` **is** archived; the old URLs for ONNX Runtime, RasterVision and Rocicorp Zero return 404; TorchGeo has **no** xView2 scoring module (it does ship `torchgeo/datasets/xbd.py` and `torchgeo/datamodules/xbd.py`); TorchMetrics has no conformal module; `maplibre/maplibre-react-native` has no PMTiles module in its tree. Anything I could not locate is not recommended below.

### 2.2 What real disaster platforms look like

Chapter 2 currently compares three imagery datasets instead of systems (review item L1). These are real, checkable systems to compare against.

| System | Status (API) | What it is | What RescueVision can take from it |
|---|---|---|---|
| [Sahana Eden](https://github.com/sahana/eden) | MIT, release 6.3 (2026-11-10) | Humanitarian resource and request management platform used by Red Cross and Red Crescent societies | How requests, pledges and warehouses are modelled; scale of a real deployment |
| [Ushahidi Platform](https://github.com/ushahidi/platform) | active; licence see repo | Crisis crowdsourcing: citizens report, analysts verify | The citizen report to verification workflow; map layers |
| [KoboToolbox KPI](https://github.com/kobotoolbox/kpi) | AGPL-3.0, release 2.026.43 (2026-11-23) | Humanitarian data collection built on XLSForm | Whether field and citizen forms should be XLSForm-based instead of hand-built |
| [IFRC GO API](https://github.com/IFRCGo/go-api) | MIT; last release 2023-08-03 | A live multi-agency disaster platform: field reports, emergencies, alerts, deployed teams | The closest operational analogue; a fair comparison target for "one shared incident" |
| [Google Person Finder](https://github.com/google/personfinder) | **archived**, Apache-2.0 | Person tracking after disasters; defined the PFIF exchange format | PFIF person-record model and its privacy practice (records expire after an event) |
| [HOT fAIr](https://github.com/hotosm/fAIr) | AGPL-3.0, release v3.1.5 (2026-11-19) | Geo-AI assisted mapping: train and run models over OSM imagery | How HOT isolates model training and inference from its web app |
| [HOT Tasking Manager](https://github.com/hotosm/tasking-manager) | BSD-2-Clause | Splits mapping work into tasks for many volunteers | Area-of-interest to task splitting, reused for tiling drone analysis |
| [Microsoft building damage assessment](https://github.com/microsoft/building-damage-assessment) | MIT, pushed 2026-08-11 | Building damage assessment toolkit | Reference implementation to compare F1 against |
| [Global Earthquake Model OpenQuake](https://github.com/gem/oq-engine) | AGPL-3.0, release v3.26.2 (2026-07-23) | Hazard and loss engine with exposure and vulnerability curves | A principled source for repair ratios instead of invented ranges |

Architect A cites `OCHA-DAP/ds-geospatial-impact-estimates` as a humanitarian reference system: the API shows 1 star and no licence. It is not one.

### 2.3 Building blocks worth reusing

| Layer | Block | Status (API unless noted) | Use in RescueVision | Verdict |
|---|---|---|---|---|
| **Core backend** | [FastAPI](https://github.com/fastapi/fastapi) | 0.165.0, MIT | Core API, workers, AI services: one language, one OpenAPI, same Pydantic models everywhere | **Adopt** |
| | [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) + [Alembic](https://github.com/sqlalchemy/alembic) | 2.1.9 MIT; 1.20.1 MIT | Versioned migrations (fixes D1) | **Adopt** |
| | [psycopg](https://github.com/psycopg/psycopg) | LGPL-3.0 | PostgreSQL driver; one transaction wrapper that sets `app.user_id` | **Adopt** |
| | [uv](https://github.com/astral-sh/uv) · [ruff](https://github.com/astral-sh/ruff) | Apache-2.0 · MIT | Locked dependencies; fixes the unpinned-notebook problem | **Adopt** |
| | [PostgREST](https://github.com/PostgREST/postgrest) | v16.6, MIT; `db-pre-request` and `db-root-spec` confirmed in its configuration docs | Instant RLS-secured CRUD from Postgres | **Considered, not chosen**: multi-step transactions, files and jobs need a real backend; keep as an option for back-office CRUD |
| | NestJS | v12.6.2, MIT | — | **Reject** (P2) |
| **Jobs** | [Procrastinate](https://github.com/procrastinate-org/procrastinate) | 3.12.0, MIT, release 2026-11-19; README: "PostgreSQL 15+ to store task definitions, manage locks", "periodic tasks, retries, arbitrary task locks" | The job queue: leasing, retries, schedules, on the same Postgres | **Adopt** |
| | [DBOS Transact](https://github.com/dbos-inc/dbos-transact-py) | 3.7.0, MIT; README: "Lightweight Durable Workflows built on top of Postgres", "checkpoint it in Postgres and automatically recover" | Alternative: durable multi-step pipelines without writing resume logic | **Alternative** if `job_steps` feels heavy |
| | [pgmq](https://github.com/pgmq/pgmq) | v1.13.2, PostgreSQL licence; `CREATE EXTENSION pgmq`; visibility timeout; archive | SQS-like semantics inside Postgres | **Alternative**; needs a custom database image |
| | [Hatchet](https://github.com/hatchet-dev/hatchet) | v0.120.24, MIT | Postgres-backed task queue with a Go server | **Reject**: another service to run |
| **Real time** | PostgreSQL `LISTEN/NOTIFY` | docs (fetched): payload "shorter than 8000 bytes", delivered only at commit | Wake-up hint for the event relay | **Adapt**: hint only, never the source of truth |
| | Redis, Kafka, NATS, EMQX (MQTT) | all active | — | **Reject** (P4, Section 2.4) |
| **AI serving** | FastAPI + ONNX Runtime or [OpenVINO](https://github.com/openvinotoolkit/openvino) | OpenVINO 2026.4.1, Apache-2.0; ONNX Runtime repository not located this session | One serving template; CPU-first | **Adopt** |
| | [LitServe](https://github.com/Lightning-AI/LitServe) | v0.2.19, Apache-2.0 | — | **Reject** (P5) |
| | [BentoML](https://github.com/bentoml/BentoML) · [Triton](https://github.com/triton-inference-server/server) | v1.4.40 Apache-2.0 · v2.75.0 BSD-3-Clause | — | **Later**, only if profiling shows a need |
| | [TorchServe](https://github.com/pytorch/serve) | **archived** | — | **Avoid** |
| | [vLLM](https://github.com/vllm-project/vllm) | v0.34.0, Apache-2.0 | Only if a vision-language model is self-hosted | **Stretch** |
| **ML engineering** | [TorchGeo](https://github.com/microsoft/torchgeo) | v0.10.1, MIT; ships xBD dataset and datamodule classes | xBD loading, geo foundation-model backbones | **Adopt** for data; **not** for scoring |
| | [xView2 scoring](https://github.com/DIUx-xView/xView2_scoring) | BSD-3-Clause, last push 2019 | The official metric (`xview2_metrics.py:255`: `0.3 * lf1 + 0.7 * df1`) | **Adopt**; stop using `xview2_approx` |
| | [DINOv3](https://github.com/facebookresearch/dinov3) | active; licence see repo | Satellite-pretrained frozen features for damage grading | **Adopt** (already in V4) |
| | [RT-DETR](https://github.com/lyuwenyu/RT-DETR) · [RF-DETR](https://github.com/roboflow/rf-detr) · [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) · [D-FINE](https://github.com/Peterande/D-FINE) | all Apache-2.0 | Permissively licensed detectors for F3 (A3) | **Evaluate two** |
| | [Ultralytics](https://github.com/ultralytics/ultralytics) | v8.4.218, **AGPL-3.0**; YOLO26 | — | **Reference only**, unless the team accepts AGPL |
| | [SAHI](https://github.com/obss/sahi) | 0.14.1, MIT | Sliced inference for small objects in aerial images | **Adopt** |
| | [ByteTrack](https://github.com/FoundationVision/ByteTrack) | MIT; last push 2024-06-19 | Tracking reference | **Adopt** as a library in the worker, not a GPU service |
| | [MLflow](https://github.com/mlflow/mlflow) · [DVC](https://github.com/iterative/dvc) | v3.18.0 · 3.67.1, Apache-2.0 | Run tracking and model registry; dataset versioning | **Adopt MLflow** for the registry gate; DVC optional |
| | [MAPIE](https://github.com/scikit-learn-contrib/MAPIE) | v1.6.0, BSD-3-Clause | Conformal prediction for damage grades and detections | **Adopt** (Section 3.5) |
| **Geospatial** | [TiTiler](https://github.com/developmentseed/titiler) | 2.4.1, MIT; COG, STAC and mosaic support | Raster tiles from cloud-optimised GeoTIFFs | **Adopt** |
| | [Martin](https://github.com/maplibre/martin) | martin-v1.16.1, Apache-2.0; PostGIS tables and functions, PMTiles, MBTiles | Vector tiles | **Optional**: only if baked tiles are not enough |
| | [PMTiles](https://github.com/protomaps/PMTiles) · [tippecanoe](https://github.com/felt/tippecanoe) | licence see repo · BSD-2-Clause | Single-file tile archives: one artefact for web and offline | **Adopt** |
| | [pgstac](https://github.com/stac-utils/pgstac) · [pystac-client](https://github.com/stac-utils/pystac-client) · [stac-fastapi](https://github.com/stac-utils/stac-fastapi) | v0.10.2 MIT · v0.9.1 · MIT | Catalogue capture sessions and rasters as STAC; ingest public pre-event imagery | **Adopt** |
| | [OpenFreeMap](https://github.com/hyperknot/openfreemap) | README: "self-host or use our public instance", "no limits on the number of map views", "no API keys" | Open-source vector basemap | **Adopt** |
| | [MapLibre GL JS](https://github.com/maplibre/maplibre-gl-js) | v6.19.0 (2026-11-17); 3D terrain in-tree; 3D Tiles documented through a three.js custom layer | 2D and 3D map on the web | **Adopt** |
| | [MapLibre React Native](https://github.com/maplibre/maplibre-react-native) | v11.5.1, MIT; Expo setup docs and example | Mobile map | **Adopt**, after an offline spike (F6) |
| | [CesiumJS](https://github.com/CesiumGS/cesium) | 1.147, Apache-2.0; hosted assets need a Cesium ion token (not re-verified) | — | **Avoid** the hosted assets; D-09 |
| | [OpenDroneMap](https://github.com/OpenDroneMap/ODM) · [NodeODM](https://github.com/OpenDroneMap/NodeODM) | v3.6.2, **AGPL-3.0**; README lists LAZ point cloud, orthophoto GeoTIFF, `--dsm` | Orthomosaic and surface model | **Conditional**: only with raw drone imagery |
| | [pgRouting](https://github.com/pgRouting/pgRouting) · [osm2pgrouting](https://github.com/pgRouting/osm2pgrouting) | v4.0.3 (2026-11-25), GPL-2.0 · v3.0.0 | Routing in the database | **Adopt** |
| | [Valhalla](https://github.com/valhalla/valhalla) | 3.9.3 | Isochrones, turn restrictions, `exclude_polygons` | **Later** |
| | [Microsoft building footprints](https://github.com/microsoft/GlobalMLBuildingFootprints) | active; ODbL (search) | Skip building segmentation where footprints exist | **Adopt** for the AOI |
| **Storage** | [RustFS](https://github.com/rustfs/rustfs) · [SeaweedFS](https://github.com/seaweedfs/seaweedfs) | 1.0.6 · 4.55, Apache-2.0 | S3-compatible object store | **Adopt one** |
| | [MinIO](https://github.com/minio/minio) | **archived**, AGPL-3.0; "NO LONGER MAINTAINED" | — | **Replace** (C9) |
| **Offline** | [PowerSync](https://github.com/powersync-ja/powersync-js) | Apache-2.0; "keeps a client-side SQLite database in sync with your backend database"; React Native SDK | Off-the-shelf Postgres to SQLite sync | **Spike against** a hand-built outbox (Section 3.6) |
| | [op-sqlite](https://github.com/op-engineering/op-sqlite) | MIT | SQLite on React Native | **Adopt** |
| | [ElectricSQL](https://github.com/electric-sql/electric) · [PGlite](https://github.com/electric-sql/pglite) · [TinyBase](https://github.com/tinyplex/tinybase) · [Automerge](https://github.com/automerge/automerge) | Apache-2.0 · Apache-2.0 · MIT · MIT | — | **Reject** for now (Section 2.4) |
| | [Expo](https://github.com/expo/expo) · [Maestro](https://github.com/mobile-dev-inc/maestro) | MIT · cli-2.12.1 Apache-2.0 | Development builds; mobile end-to-end tests | **Adopt** |
| **Security** | [fastapi-users](https://github.com/fastapi-users/fastapi-users) · [pwdlib](https://github.com/frankie567/pwdlib) | MIT · MIT | Authentication; Argon2id | **Adopt or copy** |
| **Quality** | [pytest](https://github.com/pytest-dev/pytest) · [Testcontainers](https://github.com/testcontainers/testcontainers-python) · [pgTAP](https://github.com/theory/pgtap) | 9.2.0 MIT · v4.15.0 Apache-2.0 · licence see repo | Integration tests against the real extensions; database unit tests | **Adopt** |
| | [Trivy](https://github.com/aquasecurity/trivy) · [pip-audit](https://github.com/pypa/pip-audit) · [gitleaks](https://github.com/gitleaks/gitleaks) | Apache-2.0 · Apache-2.0 · MIT | Dependency, image and secret scanning in CI | **Adopt** |
| **Operations** | [Caddy](https://github.com/caddyserver/caddy) | Apache-2.0 | TLS and reverse proxy | **Adopt** |
| | [OpenTelemetry Python](https://github.com/open-telemetry/opentelemetry-python) · [structlog](https://github.com/hynek/structlog) · [Prometheus](https://github.com/prometheus/prometheus) · [Grafana](https://github.com/grafana/grafana) · [dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter) | Apache-2.0 · see repo · Apache-2.0 · **AGPL-3.0** · Apache-2.0 | Traces, logs, metrics | **Adopt**; note Grafana's licence |
| | [pgBackRest](https://github.com/pgbackrest/pgbackrest) · [WAL-G](https://github.com/wal-g/wal-g) | 2.60.1 · v3.0.10, licences see repo | Backups and point-in-time recovery | **Adopt one** |
| | [WeasyPrint](https://github.com/Kozea/WeasyPrint) | BSD-3-Clause | HTML and CSS to PDF reports | **Adopt** |
| **Web** | [TanStack Router](https://github.com/TanStack/router) · [TanStack Query](https://github.com/TanStack/query) | MIT · MIT | Typed routes, URL state, server cache | **Adopt** (both proposals right) |

### 2.4 Considered and rejected as hype or premature

| Idea | Verdict | Reason, tied to this project |
|---|---|---|
| Microservices, Kubernetes | **Reject** | Cross-domain joins in one transaction are the core logic (`evaluate_hazard_rules` touches seven tables). Compose on one machine is enough for a pilot; `k3s` only if a host requires it. |
| Kafka, NATS | **Reject** | Pilot volume is tens of jobs and hundreds of events per minute. Postgres holds the queue and the log. |
| MQTT for the field channel | **Reject** | Attractive on paper (persistent sessions, queued messages), but a relay with per-device cursors over the event log gives the same catch-up without a broker. Backgrounded phones cannot hold connections either way; push notifications remain necessary. |
| Redis | **Reject** | P4. |
| gRPC between services | **Reject** | HTTP with JSON plus binary tile bodies is enough; OpenAPI codegen already exists in the design. |
| Writing services in Rust, Go or Elixir | **Reject** | Take them as binaries: Martin, tippecanoe, Caddy, ODM, RustFS. The team writes Python and TypeScript. |
| Full event sourcing | **Reject; adopt "lite"** | Rebuilding all state from events with RLS is a large engineering cost. Keep current state in tables and add an append-only event log as the timeline. |
| 3D Gaussian splatting | **Reject** | Heavy GPU training, weak georeferencing, and no raw imagery to train on (F8). |
| WebGPU shaders for swipe and confidence sliders | **Reject** | A before/after swipe is two raster sources with a clip path in MapLibre; a confidence slider is a filter on vector features. Neither needs WebGPU. |
| CRDT documents (Automerge, Yjs) | **Reject** | Field records are append-only events with a few status fields owned by a role, not concurrently edited documents. An idempotent outbox is simpler and deterministic. |
| Running Postgres in the browser or on the phone (PGlite) | **Reject** | No PostGIS, pgRouting or RLS parity. |
| Gazebo, ROS 2, PX4 simulation | **Reject** | A second capstone project with a 3 to 6 week entry cost (`docs/claude_view.md:40`). It validates geometry, not perception accuracy. Replace with a scenario replayer over the event log. |
| 7B-teacher distillation | **Reject on current hardware** | `BLOCKED_INSUFFICIENT_MEMORY` on the only GPU available (A1). |
| Pixel-level satellite and drone fusion | **Reject** | A resolution gap of one to two orders of magnitude and different latencies. Fuse by co-registering layers on one map. |
| Commander copilot with tool use over the database | **Stretch, guarded** | Useful only if it cannot act and never sees personal data. Two narrow uses are defensible (Section 3.5). |
| Meshtastic or other LoRa mesh | **Stretch** | Cheap radios, a real benefit when cellular fails, but a hardware side-project and a radio-licence question. The realistic answer to "no cellular" is a command-post local network. |
| On-device detection on the phone or drone controller | **Stretch** | Worth a two-week spike after the server path works. |
| Valhalla | **Later** | pgRouting in the database keeps closures and routes in one transaction. |
| "Similar past cases" (pgvector) | **Cut from MVP** | FR-RP-10 is optional and the feature has no user story in the use cases. |

### 2.5 Facts that constrain the design

| Fact | Source | Consequence for RescueVision |
|---|---|---|
| "The ground around power lines – up to 35 feet away – may be energized." | [ESFI](https://www.esfi.org/downed-power-lines) (search) | The relevant distance is about 10.7 m from a **downed** line. The 30 m buffer around any overhead line (D6) is a guess, not guidance. |
| 6 inches of water can cause loss of control in most cars; 12 inches floats many vehicles; 2 feet of rushing water carries away SUVs and trucks. | [NWS Turn Around Don't Drown](https://www.weather.gov/tsa/hydro_tadd) (search) | Defaults for `vehicles.max_water_depth_cm`: 15 cm for ordinary vehicles. The demo seeds 15 cm for an ambulance and 50 cm for a fire truck (`database/seed/02_demo_scenario.sql:71-74`); the 50 has no cited basis. |
| Official xView2 score is `0.3 × localization F1 + 0.7 × harmonic mean of four damage F1`. | `DIUx-xView/xView2_scoring`, `xview2_metrics.py:248-255` (ran) | Report this metric only, on the untouched test split. |
| FloodNet imagery was "captured after the hurricane Harvey". | [arXiv 2012.02951](https://arxiv.org/abs/2012.02951) (fetched) | One hurricane, one region: no evidence of transfer to Egypt (already stated in `docs/tier1_papers_summary.md`). `docs/PROJECT_ANALYSIS.md:238` names the wrong hurricane. |
| SeaDronesSee: about 5,630 UAV images of open water; classes swimmer, floater, boat, jetski, buoy, life-saving appliances; a MOT subset. | [arXiv 2105.01922](https://arxiv.org/abs/2105.01922), WACV 2022 (search; counts unverified) | The closest public analogue to "people in flood water"; should be in the F3 training mix. |
| SARD: 1,981 images; HERIDAL: roughly 1,700 images, counts vary by source. | IEEE DataPort; search (unverified) | Training corpora for F3 are in the low thousands and show people in terrain, not in urban debris. Expect low recall in Cairo; measure it. |
| Microsoft building footprints: about 1.4 billion polygons, ODbL; reported to cover every African country except Cabo Verde. | search (unverified by me; check `dataset-links.csv` for `EGY`) | Do not train a building segmenter for the AOI. Use footprints as given and spend the effort on damage. |
| `NOTIFY` payload "must be shorter than 8000 bytes"; notifications are delivered only at commit. | [PostgreSQL docs](https://www.postgresql.org/docs/current/sql-notify.html) (fetched) | Events must live in a table and carry a reference; `NOTIFY` may carry only the id. |
| `ultralytics` is AGPL-3.0; README: "Request an Enterprise License for commercial use". | README (ran) | A legal decision, not a technical one (A3). |

---

## 3. Proposed architecture

### 3.1 Vision

RescueVision becomes a **safety-first incident twin**. One PostgreSQL database is the brain and the memory: it holds the operational record, decides who may see and change what, evaluates compound-hazard rules in the same transaction as the facts that trigger them, and appends everything that matters to one ordered incident event log. That log is the only spine; live updates, offline synchronisation, after-action replay and regression tests are all consumers of it, each with a cursor. AI models are interchangeable observers behind one contract: they publish typed, calibrated, reviewable observations into the same database and can be switched off without the platform noticing. The field app works with no network and catches up from the same log. The whole core runs on CPU, on one machine, in six containers.

What is unique here is not a technology. It is that three properties the two proposals promise but do not build — an alert that is atomic with the report that caused it, a route that cannot cross a live danger zone, and a field device that never misses an alert — become **invariants of the data model and are proved by executable tests**. That is a defensible contribution for a graduation project and a demonstrable one.

### 3.2 Seven rules

1. **The database is the brain; everything else is replaceable.** Keep the 56-table model.
2. **Commit the effect with the cause.** A hazard and the alert it triggers are one transaction.
3. **Derive, never restore.** Routability is computed from live alerts and the latest observation. Nothing is mutated and put back.
4. **One ordered log; every consumer keeps a cursor.** Push, sync, replay and tests read the same events.
5. **AI observes, people decide.** No model is activated without evidence; confidence is calibrated.
6. **CPU first.** The GPU, if one is rented, is an accelerator.
7. **No component without an owner and a reason.** Six containers in the core profile.

### 3.3 Components

```
                ┌────────────── browser (React + Vite, MapLibre) ──────────────┐
                │  field phone (Expo dev build: SQLite outbox, offline tiles)  │  citizen PWA
                └───────────────┬─────────────────────────────┬───────────────┘ ┌────┐
                        HTTPS    │ REST (writes), SSE (events, with cursor)     │    │
                         S3      │ presigned uploads/downloads                    │    │
                ┌────────────────▼──────────────────────────────────────────────▼────┴──┐
                │ caddy  TLS · static web build · rate limits · reverse proxy           │
                └───┬──────────────────┬────────────────────────┬───────────────┬───────┘
                    │                  │ tiles (COG → PNG)      │ S3 range GET  │
     ┌──────────────▼───────┐  ┌───────▼────────┐  ┌────────────▼─────────────┐ │
     │ core-api  (FastAPI)  │  │ titiler        │  │ objects  (RustFS /      │ │
     │ auth · RLS context   │  └───────┬────────┘  │ SeaweedFS, S3 API)       │◄┘
     │ REST · SSE · sync    │          │           └────────────▲─────────────┘
     └──────────────┬───────┘          │                        │
                    │ one image        │                        │
     ┌──────────────▼──────────────────┴──┐   HTTP, model contract   │
     │ worker  (same image as core-api)   │──────┐   ┌──────────────┴──────────┐
     │ queue consumer · pipeline steps    │      ├──►│ ai-damage │ ai-person │ │
     │ event relay · tile baker · reports │      │   │ ai-scene  (one template)│ │
     │ re-routing                         │      │   └─────────────────────────┘ │
     └──────────────┬─────────────────────┘      │        profile `ai-cpu` | `ai-gpu`
                    │ rv_worker                   │   ┌────┴──────────────┐
     ┌──────────────▼───────────────────────────┴─┐ │ nodeodm (optional, AGPL) │
     │ db  PostgreSQL 18 + PostGIS + pgRouting     │ └──────────────────────────┘
     │     + pgvector · RLS · hazard engine        │
     │     · incident_events (the spine)           │      profile `obs`: prometheus, grafana
     └─────────────────────────────────────────────┘
```

| Container | Profile | Built from | Responsibility | Why this and not the alternative |
|---|---|---|---|---|
| `caddy` | core | official image | TLS, serves the web build, rate limits, proxy | One binary for edge and static files, so the web app needs no Node server |
| `core-api` | core | `rescuevision/app` | Sign-in, REST commands and queries, sets `app.user_id` per transaction, SSE with cursor, sync endpoints, presigned URLs | FastAPI (decision 1) |
| `worker` | core | `rescuevision/app`, second command | Queue consumer, pipeline steps, event relay, tile baker, PDF reports, re-routing | Same image as the API: one build, shared models, half the maintenance |
| `db` | core | `rescuevision/db` (`FROM postgis/postgis:18-3.6`, add pgRouting and pgvector) | Everything in rules 1 to 4 | Pin the three extensions in one image; tags `18-3.6` and `0.8.x-pg18` exist on Docker Hub (ran); pgRouting needs a package install (verify for the image's Debian release) |
| `objects` | core | RustFS or SeaweedFS | Imagery, rasters, tiles, model bundles, reports | S3 is the contract; the store is replaceable (C9) |
| `tiles` | core | TiTiler | Raster tiles and crops from cloud-optimised GeoTIFFs | Decides once how a multi-gigabyte orthomosaic is streamed |
| `ai-damage`, `ai-person`, `ai-scene` | ai | `rescuevision/ai`, one template, one model bundle each | Building damage; person detection; flood, road and hazard segmentation plus embeddings | The owner's rule is "every model isolated, in Docker, behind an API". Three model families satisfy it without nine copies of a CUDA context. Confirm the reading with the owner |
| `nodeodm` | photogrammetry | official image, AGPL-3.0 | Orthomosaic and surface model from raw frames | Only when raw imagery exists |
| `prometheus`, `grafana` | obs | official images | Metrics and dashboards | Section 3.10 |
| `martin`, `mlflow` | optional | official images | Live vector tiles if baked tiles are not enough; run tracking | Not in the default path |

**Count:** six containers to run the core, eleven for the full demonstration with AI and monitoring. The platform plan lists nine (without monitoring), Architect A fourteen plus three.

### Decisions where the proposals disagree, or are silent

**Decision 1 — core backend: FastAPI, not NestJS.**

| Criterion | FastAPI (Python) | NestJS (TypeScript) |
|---|---|---|
| What the team already has | `api/`, all ML code, V4's pytest suite | README files |
| Contract with the clients | `frontend/tooling/README.md:5` and `frontend/packages/api/README.md:28` already generate types from FastAPI's `/openapi.json` | A new generator and a rewrite of that tooling |
| Geospatial, raster and PDF work | rasterio, shapely, pyproj, WeasyPrint, all in the worker's language | No equivalent; the worker has to be Python in any case |
| Logic beside SQL | One language next to RLS policies and PL/pgSQL | Two |
| Capacity | Enough for the stated 200 concurrent users (NFR-PF-06); not measured here | More raw throughput; not needed |
| Cost of being wrong | One image and one lock file | Two backends for six students |

**Decision 2 — object store:** the S3 API is the contract; RustFS or SeaweedFS runs in Compose; a hosted S3 bucket can replace it without a code change.

**Decision 3 — queue:** Procrastinate owns leasing, retries and schedules in the same Postgres. `processing_jobs` stays as the record the user sees. A small `job_steps` table gives resume: each step writes its output under a deterministic key and records the hash of its input, so a restarted job skips finished steps. DBOS Transact is the alternative if the team prefers durable workflows as a library.

**Decision 4 — live updates:** SSE for the web, carrying the event `id`; the browser's `Last-Event-ID` header resumes after a drop. The mobile app uses the same `/events?since=` endpoint when it comes to the foreground. WebSocket stays available for foreground streaming if a spike shows SSE is awkward in React Native; the contract is the event envelope, not the transport.

**Decision 5 — tiles:** analysis outputs are baked once per run into PMTiles (one file serves the web map and the offline pack); live operational layers (positions, alerts, routes, cases) are GeoJSON from the API, small and under the same RLS transaction. This removes the tile-server hole Architect A warns about: a vector tile server that connects to Postgres directly bypasses RLS.

**Decision 6 — AI serving:** one FastAPI-based template. The worker batches tiles itself.

**Decision 7 — one map engine:** MapLibre on web and mobile.

**Decision 8 — offline sync:** a hand-built outbox protocol over the event log (Section 3.6), with PowerSync as the fallback if the mobile owner is part-time. Gate: end of the Phase 1 spike.

### 3.4 The spine: the incident event log and a repaired hazard engine

#### 3.4.1 The log

```sql
CREATE TABLE incident_events (
  id              bigint GENERATED ALWAYS AS IDENTITY,
  recorded_at     timestamptz NOT NULL DEFAULT now(),
  incident_id     uuid        NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  stream          text        NOT NULL,               -- alert | hazard | case | mission | route | analysis | sync
  type            text        NOT NULL,               -- alert.raised, route.replaced, case.updated …
  subject_id      uuid,                               -- the record the event is about
  actor_user_id   uuid,                               -- NULL means the system
  client_op_id    uuid,                               -- set when an offline operation caused it
  payload         jsonb       NOT NULL DEFAULT '{}',  -- kept under 8 KB; bulky bodies by storage key
  schema_version  smallint     NOT NULL DEFAULT 1,
  occurred_at     timestamptz NOT NULL,
  PRIMARY KEY (id, recorded_at)
) PARTITION BY RANGE (recorded_at);
CREATE INDEX incident_events_log_idx ON incident_events (incident_id, id);
```

- Writers append in the transaction that changes state. A statement trigger sends `NOTIFY incident_events, '<max id>'` at commit. **Polling is the guarantee and the notification is the optimisation**: a relay that missed a notification still reads `id > cursor` on its next tick.
- RLS: staff may read events of incidents their agency has joined; only security-definer functions and the worker may append; no role may update or delete.
- Personal data stays out of payloads. An event says "case `X` changed"; the client fetches details under RLS. Push notifications carry the event type and ids only.

#### 3.4.2 The relay

One coroutine in the worker: read up to 500 events after the cursor, send each to the sessions allowed to see its incident, advance the cursor, sleep until a notification or one second. Expo push is sent for `alert.raised`, `sos.raised`, `route.invalidated` and `route.replaced`. The relay's lag, newest event id minus newest id sent, is the metric that makes NFR-PF-04 measurable (O6).

#### 3.4.3 Hazard engine, version 2

Seven changes to `12_hazard_engine.sql` and its policies. They fix C4, C5, C6, D2, D3, D4 and D7.

1. **Evaluate on write, as the system.** The engine becomes `SECURITY DEFINER` with a fixed `search_path`, called by statement triggers. The caller still needs the right to write the hazard or the asset, so the right to report *is* the right to trigger evaluation, and the effect is atomic with the report. Audit rows keep the responder's identity because `app.audit()` reads `app.current_user_id()`.

```sql
ALTER FUNCTION evaluate_hazard_rules(uuid)
  SECURITY DEFINER SET search_path = public, pg_temp;

CREATE OR REPLACE FUNCTION app.after_hazard_input() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE inc uuid;
BEGIN
  FOR inc IN SELECT DISTINCT incident_id FROM changed LOOP
    PERFORM evaluate_hazard_rules(inc);
  END LOOP;
  RETURN NULL;
END $$;

CREATE TRIGGER hazards_evaluate
  AFTER INSERT OR UPDATE OF status, geom, expires_at ON hazards
  REFERENCING NEW TABLE AS changed FOR EACH STATEMENT
  EXECUTE FUNCTION app.after_hazard_input();

CREATE TRIGGER infrastructure_assets_evaluate
  AFTER INSERT OR UPDATE OF power_state, geom, asset_type ON infrastructure_assets
  REFERENCING NEW TABLE AS changed FOR EACH STATEMENT
  EXECUTE FUNCTION app.after_hazard_input();
```

2. **Merge per asset.** Before creating an alert for a hazard and a partner asset, look for a live alert of the same rule that already names that asset. If one exists, add the new hazard as a source and enlarge the danger zone instead of opening a second alert.

```sql
SELECT s.alert_id INTO v_existing
FROM compound_alert_sources s
JOIN compound_alerts a ON a.id = s.alert_id
WHERE s.asset_id = p.id AND a.rule_id = r.id AND a.status IN ('ACTIVE','ACKNOWLEDGED')
LIMIT 1;

IF v_existing IS NOT NULL THEN
  INSERT INTO compound_alert_sources (alert_id, hazard_id) VALUES (v_existing, h.id)
  ON CONFLICT (alert_id, hazard_id) WHERE hazard_id IS NOT NULL DO NOTHING;
  UPDATE compound_alerts
     SET danger_zone = ST_Multi(ST_Union(danger_zone, v_zone))
   WHERE id = v_existing;
END IF;
```

3. **Derive routability; stop restoring.** `road_segments.cost` and `reverse_cost` keep base travel times only and are never touched by alerts. The edge set is a function that follows the report's own formula (§3.3.8.3): a direction is unusable if the segment is `BLOCKED`, intersects a live danger zone, or is `FLOODED` deeper than the vehicle can cross.

```sql
CREATE OR REPLACE FUNCTION routing.edges(p_incident uuid, p_max_depth_cm integer DEFAULT 0)
RETURNS TABLE (id bigint, source bigint, target bigint, cost float8, reverse_cost float8)
LANGUAGE sql STABLE AS $$
  SELECT s.id, s.source, s.target,
         CASE WHEN closed THEN -1 ELSE s.cost         END,
         CASE WHEN closed THEN -1 ELSE s.reverse_cost END
  FROM road_segments s
  CROSS JOIN LATERAL (
    SELECT (s.condition = 'BLOCKED'
         OR (s.condition = 'FLOODED'
             AND (s.water_depth_cm IS NULL OR s.water_depth_cm > p_max_depth_cm))
         OR EXISTS (SELECT 1 FROM compound_alerts a
                    WHERE a.incident_id = s.incident_id
                      AND a.status IN ('ACTIVE','ACKNOWLEDGED')
                      AND ST_Intersects(a.danger_zone, s.geom))) AS closed
  ) f
  WHERE s.incident_id = p_incident;
$$;
```

   One deliberate addition to the report's formula: a flooded segment whose depth is unknown counts as too deep, and a vehicle with no `max_water_depth_cm` is treated as able to cross none. That follows the report's own rule that missing information is "shown as such, never as safe" (Table 3-40). Section 3.2 of the report (the requirements) should say so: under its current wording a `NULL` depth does not satisfy "greater than *d*(*v*)", so such a segment reads as usable, and no code computes the cost from the depth today (`07_roads.sql:62` leaves it to a routing service that does not exist yet).
   Consequences: the `AND condition <> 'HAZARD_CLOSED'` clause in `07_roads.sql:73` is removed, so observations always update the cache; `resolve_compound_alert` only changes the alert's status and appends an event; `alert_closed_segments` keeps `(alert_id, segment_id, covered_at)` for display and loses `prev_*`. The two bugs in C5 cannot occur because there is no stored previous state to restore in the wrong order or from before a newer observation.

4. **Warn the people at risk.** Recipients are responders inside the zone, within a configurable `warn_radius_m` of it, assigned to a mission whose target is inside it, and assigned to an invalidated route. Position age is shown next to the name.

5. **Re-route.** `routes` gains `supersedes_route_id`. The engine still marks affected routes `INVALIDATED` and appends `route.invalidated`. A worker task then plans a replacement with `routing.edges` for the team's vehicle, inserts it as the successor and appends `route.replaced`, or `route.no_safe_route` with the blocking closures.

6. **Let citizens reach the engine.** A `SECURITY DEFINER` function, callable with `case.verify`, turns a verified citizen request into a hazard row with `origin = 'CITIZEN_REPORTED'`, so the conversion no longer depends on the worker role.

7. **Append events.** `alert.raised`, `alert.extended`, `alert.resolved` and `route.invalidated` are written in the same transaction.

#### 3.4.4 What "safe" means, as tests

Each line becomes a test that runs on every commit against the demo scenario and on randomised orderings.

| ID | Invariant | Fails today because of |
|---|---|---|
| I1 | No active route intersects a live danger zone. | Re-routing does not exist (C6) |
| I2 | Every live hazard within range of a matching operand has an alert, or a recorded suppression reason. | Evaluation is a manual call (D2) |
| I3 | A Field Responder can report a hazard and receive the alert for it. | Security invoker (C4) |
| I4 | After any sequence of overlapping alerts raised and resolved in any order, a segment is usable if and only if no live alert covers it and its latest observation allows it. | Stored previous state (C5) |
| I5 | An observation made during a closure wins when the closure ends. | Observations ignored while closed (C5) |
| I6 | No role except the migration role can update or delete `audit_log`. | `service_all` on `audit_log` (C8) |
| I7 | A hazard report and its alert commit together or not at all. | Two-transaction flow (C4) |
| I8 | Relaying every event after any restart loses none and repeats none. | No log (P3) |

### 3.5 AI architecture

#### Serving: one template, three containers, no database access

| Endpoint of every AI container | Purpose |
|---|---|
| `POST /v1/{task}:predict` | A batch of tiles or crops (binary PNG, JPEG or NumPy body) with the run id, the tile's geotransform and its ground resolution. Returns typed observations with a confidence and a calibrated set each, and the `model_version`. |
| `GET /v1/model-info` | Name, version, SHA-256 of the weights, dataset digests, evaluation metrics, input specification (bands, normalisation, resolution range), label schema version, licence. |
| `GET /healthz`, `GET /readyz` | The process is alive; the weights are loaded and a self-test tensor passes. |

- The API and the worker never import torch. The worker checks `model-info` against the registry row before the first request of a run, so FR-IM-07 becomes a verified fact instead of a stored string.
- **AI containers hold no database credentials.** Only the worker writes results. That single rule removes most of the damage an AI container can do (C8).
- Timeouts, bounded retries and a circuit breaker. When `readyz` fails, jobs wait and the console shows "AI unavailable"; maps, cases and routing continue (NFR-RL-04).
- Each bundle states the sensor and ground resolution it was trained for. The worker refuses tiles outside that range instead of guessing (A4).

#### CPU first

Export every model to ONNX and run it with ONNX Runtime or OpenVINO; measure quantisation on real tiles. Targets for the demonstration area, **to be measured and not promised**: seconds per frame for detection, minutes for a small orthomosaic. The GPU image is the same container with another base image and device setting. A GPU should be rented only for the final load test and for recording results; that purchase needs the team's decision now, because NFR-PF-05's targets are written as if GPUs were present.

#### Versioning: a registry that refuses unevidenced models

MLflow (self-hosted, Postgres as backend store, S3 for artefacts) tracks runs. Each run records the code commit, the package version, the dataset digests and the metrics from the official scorer. Promoting a run writes a model bundle whose `manifest.json` is the model card. The registry enforces it:

```sql
ALTER TABLE ai_models
  ADD COLUMN weights_sha256  text,
  ADD COLUMN eval_set_digest text,
  ADD COLUMN eval_metrics    jsonb,
  ADD COLUMN code_commit     text,
  ADD COLUMN licence         text,
  ADD COLUMN status          model_status NOT NULL DEFAULT 'candidate';

ALTER TABLE ai_models ADD CONSTRAINT ai_models_active_needs_evidence CHECK (
  NOT is_active OR (weights_sha256  IS NOT NULL
                AND eval_set_digest IS NOT NULL
                AND eval_metrics    IS NOT NULL
                AND status = 'validated'));
```

The seed changes accordingly: all nine rows become `is_active = false` until a bundle exists.

#### Evaluation protocol

1. The official scorer. For xBD, `DIUx-xView/xView2_scoring`, never `xview2_approx`.
2. A frozen test split. Model, threshold and post-processing choices are made on the validation split only (C10).
3. A geographic hold-out: whole disasters or regions left out, plus a small set collected in Egypt.
4. Calibration: a reliability diagram and the empirical coverage of the stated confidence level.
5. Slices by ground resolution and by visibility.
6. Every number that enters the report carries a run id, and the table of record is committed to `main`.

#### Calibrated confidence and the review queue

- **Damage grades:** conformal prediction (MAPIE) on the validation split gives each building a *set* of grades with a guaranteed marginal coverage, for example 90%. A single-grade set goes to "quick confirm". A two-grade set such as {Major, Destroyed} goes to the front of the queue with both shown.
- **Detections:** calibrate the confidence and fix the operating threshold for a target false-positive rate per image on the validation split; report recall at that threshold.
- **Why it matters:** D-07 already admits that review adds work for Analysts. A queue ordered by calibrated uncertainty turns that cost into a measurable result: percentage needing review and time to review, at fixed recall.
- The map shows the set, not one colour.

#### Two lanes for imagery (fixes D9)

- **Accurate lane** (as the report designs): orthomosaic, tiled inference, polygons, minutes to hours.
- **Fast lane:** single frames, detection, geolocation from the camera pose with a flat-ground assumption, published after seconds with a large uncertainty radius and marked provisional. The accurate lane supersedes it later.
- Schema changes: `inference_runs.post_raster_id` becomes nullable with a constraint that at least one input is referenced; tracks belong to the incident with a link to the run on each detection; `person_detections.visibility`, `occlusion_ratio` and `posture` become nullable with a source and a confidence (C11).

#### Model plan by task

| Task | Ship first | Research track | Do not |
|---|---|---|---|
| Building damage (F1) | Footprints from OSM or Microsoft where they exist; a frozen DINOv3 satellite backbone with a light head; the official xView2 score on the frozen test split | V4's paired multiscale model | The 7B teacher (A1) |
| Person detection (F3) | One Apache-2.0 detector (RT-DETR, RF-DETR, YOLOX or D-FINE) fine-tuned on SARD, HERIDAL and SeaDronesSee, with sliced inference (SAHI) | A second detector for comparison; the visibility attributes | Claiming partial-visibility detection before the annotated test set exists |
| Tracking (F4) | ByteTrack in the worker, on CPU, per flight | Re-observation from several azimuths to suppress static false positives | Treating stationarity as evidence of injury (A6) |
| Flood, road and hazard segmentation (F2) | SegFormer on FloodNet and RescueNet, plus imagery the team collects | Elevation-aware rules (stretch) | — |
| Restoration cost (F1) | A deterministic cost model with a sensitivity output | Repair ratios from OpenQuake-style vulnerability curves | Calling it AI (A5) |
| Similar past cases (FR-RP-10) | Nothing in the MVP | — | Spending weeks on it |

#### Vision-language models: two guarded uses, both stretch

1. Drafting the narrative of a situation report from a frozen snapshot. The model may phrase; every number is injected and validated by code.
2. A "second reader" that ranks the review queue and captions crops.

Neither acts, neither sees personal data, and the model is self-hosted or used under a data-processing agreement. A free-text copilot with tool use over the operational database is not worth its risk for this project.

### 3.6 APIs and communication

| Path | Mechanism | Why |
|---|---|---|
| Client writes | `POST` over HTTPS with an `Idempotency-Key` | One RLS transaction per command; offline replay is safe |
| Client reads | REST/JSON, OpenAPI 3.1 → `openapi-typescript` | Already the frontend's design |
| Live updates | SSE of events with a cursor, `GET /v1/incidents/{id}/events?since=` | Resumable, proxy-friendly, one direction |
| Push to phones | Expo push with a data-only payload | Background delivery; content is fetched after sign-in |
| Positions | `POST /v1/positions:batch` | Idempotent on `(device_id, recorded_at)` |
| Uploads | Presigned multipart S3 URLs with the checksum declared up front | Large files never pass through the API (as the report proposes) |
| Worker to AI | HTTP, JSON plus binary tile bodies | The owner's isolation rule |
| Worker to OpenDroneMap | Its REST API | — |
| Raster tiles | TiTiler over S3 | — |
| Vector layers | PMTiles from object storage; live layers as GeoJSON from the API | Decision 5 |
| Alerts | The event log | Never a bare `NOTIFY` payload |

**Event envelope**

```json
{ "id": 48213, "incident_id": "0192…", "type": "alert.raised",
  "subject_id": "0193…", "occurred_at": "2026-11-25T14:02:11Z", "schema_version": 1,
  "payload": { "title": "Electrified Water – El-Nile Street", "severity": 5,
               "roads_covered": 3, "routes_invalidated": 1 } }
```

**Sync protocol (the design the ERD specification left out)**

- **Push.** The device keeps `client_ops(device_id, op_seq, kind, body, if_match, created_at, state)`. `POST /v1/sync/push` sends a batch. The server keeps `(device_id, op_seq)` as a key, applies each operation in the usual RLS transaction and answers per operation with `applied` or `rejected` plus a code. A replay after a crash changes nothing.
- **Pull.** `GET /v1/sync/pull?incident=…&since=<event id>` returns the later events and the new cursor. If the device is too far behind or has no cursor, the server returns a snapshot and a cursor taken in one repeatable-read transaction, so the two agree.
- **Deferred authorisation.** An operation accepted on a device can be rejected at sync: the agency left the incident, the mission was reassigned, a role check fails. The app must show the rejection to the responder. No document addresses this (F4).
- **Conflicts.** Appends never conflict. Status changes carry `if_match`, the `updated_at` the device last saw; a mismatch is rejected with the current record attached.
- **Offline warnings.** The device keeps the last danger zones and runs a local geofence alarm labelled with the age of the data ("zones as of 14:32, 40 minutes old"). It cannot know about a hazard raised while it was offline, and the interface must say so.

### 3.7 Three data flows

**Drone upload → damage map**

1. An Analyst creates a capture session; the API returns presigned multipart URLs; the browser uploads frames directly to object storage.
2. The browser registers the files with SHA-256 values. In one transaction the API inserts the `images` rows, the `processing_jobs` row and the queued job on the same connection, and answers `202` with the job id.
3. **STITCH** (raw overlapping frames only; satellite tiles skip it). The worker calls OpenDroneMap and writes a cloud-optimised orthomosaic and a surface model. A restarted job skips the step when the outputs already exist under the deterministic keys.
4. **ANALYZE.** The worker tiles the area in a metric grid, reads windows from the COG, sends batches to `ai-damage`, checks `model-info` against the registry, creates the `inference_runs` row and writes pending `building_assessments` with calibrated sets, plus cost estimates.
5. **TILE and REPORT.** Damage polygons and masks are baked to PMTiles; the report snapshot is drafted.
6. Each step appends `job.progress`; `analysis.completed` reaches the console through the relay; the map loads the new PMTiles and the Analyst opens the review queue.

**Flood report → Electrified Water alert**

1. A responder files a flood report, online or from the offline queue.
2. One transaction: the hazard row is inserted; the trigger runs the engine as the system; an energised asset is within range; the alert is created or merged; covered segments and invalidated routes are recorded; notifications are inserted; `alert.raised` and `route.invalidated` are appended. This takes milliseconds.
3. The relay delivers within a second. Consoles show the banner; phones in or near the zone receive a push.
4. The worker re-plans each invalidated route with `routing.edges` and appends `route.replaced`, or `route.no_safe_route` with the blocking closures.
5. When the utility confirms the cut and a commander resolves the alert, routability follows by itself: the road is usable again unless another live alert covers it or a newer observation says otherwise.

**Responder offline in the field**

1. Before losing coverage the app holds a snapshot (missions, cases, routes, live danger zones for the area), an offline basemap pack and a cursor.
2. Offline: case updates, hazard reports and positions go to the outbox with UUIDv7 ids and sequence numbers; the map shows danger zones with their age; an SOS is stored and sent at the first contact with any network.
3. On reconnect (cellular, or the command post's local network): push the outbox, receive per-operation results, pull the events after the cursor. Alerts raised while offline are replayed first; an invalidated route arrives with its replacement.
4. Rejected operations are shown, not dropped. The audit log records the device time and the apply time.

### 3.8 Frontend web, mobile and maps

**Web: React + Vite, TanStack Router and Query, MapLibre GL JS**

- The incident map is the centre, as the report designs. Map state (incident, viewport, layers, filters, selection) lives in validated URL search parameters.
- Layers: OpenFreeMap or a self-hosted Protomaps basemap; the team's orthomosaic through TiTiler; damage and detections as PMTiles; live layers as GeoJSON refreshed by events.
- 3D: MapLibre terrain with open terrain tiles and footprints extruded from known heights or the surface model. OpenDroneMap meshes, if any, through a 3D Tiles custom layer. No Cesium ion assets (D-09).
- Review queue ordered by calibrated uncertainty, with the model's alternatives shown.
- Before/after swipe: two raster sources and a clip path.
- Arabic and right-to-left from the first sprint (IR-UI-07), including a test of Arabic label shaping on the map.
- Vertical slices by feature, as `frontend/README.md` intends. One vocabulary in `packages/contracts`, generated from the database enums and the event schema. Delete the legacy `dashboard/`.

**Mobile: Expo development build, never Expo Go**

- MapLibre React Native, op-sqlite for the local store and the outbox, expo-location for background positions, expo-notifications for push, expo-secure-store for tokens.
- **Week-one spike (three days): an offline basemap on a development build.** Candidates: the PMTiles protocol; bundled raster tiles through a local file template; a georeferenced image source. Take the first that works. No mobile commitment is safe before this (F6).
- Foreground: SSE or WebSocket with a cursor. Background: push, then pull on wake.
- Position rate adapts to the mission (seconds on an active mission, slower otherwise) with on-device track simplification.
- One-hand operation, large targets, an offline indicator and a count of queued items, as Table 3-45 specifies.

**Citizen channel.** A small progressive web app: phone number, a one-time code by SMS (codes hashed, attempt limits kept in a table), request type, location, photo. EXIF is stripped on upload.

### 3.9 Database changes at a glance

| # | Change | Fixes |
|---|---|---|
| 1 | `evaluate_hazard_rules` becomes `SECURITY DEFINER`; statement triggers on `hazards` and `infrastructure_assets` call it | C4, D2 |
| 2 | Merge a new hazard into a live alert that already names the same asset | D3 |
| 3 | `routing.edges(incident, max_depth_cm)`; road costs are never mutated; `prev_*` columns and the `HAZARD_CLOSED` guard on observations go; `resolve_compound_alert` only changes status and appends an event | C5 |
| 4 | `routes.supersedes_route_id` and a re-routing task | C6 |
| 5 | `app.promote_citizen_request()` | D4 |
| 6 | Notification recipients: inside, within `warn_radius_m`, mission target inside, assigned to an invalidated route | D7 |
| 7 | `hazard_rules.conditions jsonb` and per-type power-state semantics | D5, D6 |
| 8 | `incident_events` table, a relay cursor table, a notify trigger | P3, P4 |
| 9 | `processing_jobs`: `priority`, `attempts`, `max_attempts`, `lease_until`, `heartbeat_at`, `cancelled_at`, `error_code`, `parent_job_id`; a `job_steps` table; `job_type` gains `DETECT` and `EXPORT`; `job_status` gains `RETRY_WAIT`, `CANCELLED`, `DEAD` | C7 |
| 10 | `rv_worker` loses `UPDATE` and `DELETE`; least-privilege grants; `audit_log` append-only for every role | C8 |
| 11 | `ai_models`: evidence columns, a `model_status` enum (`candidate`, `validated`, `active`, `retired`) and the activation constraint; seeds become inactive | C3, D10 |
| 12 | `inference_runs.post_raster_id` nullable with input links; tracks belong to the incident; detection attributes nullable with a source and a confidence | D9, C11 |
| 13 | Alembic migrations; `build.sh` reserved for scratch databases | D1 |
| 14 | Demo seed: routes are inserted before hazards, because triggers now fire at insert time | — |
| 15 | One-time-code table with attempt counters; `client_ops` table for sync | O4, F4 |
| 16 | The one-incident assumption of roads and buildings is documented now and split into a shared base layer later | D8 |

### 3.10 Deployment, observability, security, testing

**Deployment**

- `docker compose up` starts the core profile. Overlays: `compose.ai.yaml`, `compose.obs.yaml`, `compose.photogrammetry.yaml`.
- Four images to build and own: `rescuevision/app`, `rescuevision/db`, `rescuevision/ai`, and the web build copied into Caddy.
- Three environments: development (laptop), demonstration (one machine with 16 GB or more), pilot (one virtual machine, hosted S3, managed PostgreSQL optional). No Kubernetes.
- **Command post in a box** (stretch): the same core profile on a laptop with a Wi-Fi access point. Phones sync to it over the local network, and it forwards its event log to the cloud when a link returns. This is the realistic answer to "the cellular network is down".
- Migrations run on deploy as a one-off job. `DROP DATABASE` is never used outside scratch databases.
- Backups: pgBackRest or WAL-G with daily base backups and continuous WAL archiving; object versioning in S3. A restore drill into a scratch database, with a check that every `storage_key` resolves to an object, before any exercise (NFR-RL-05).

**Observability: one metric per promise**

| Requirement | Metric | Proposed target (to be agreed with the team) |
|---|---|---|
| NFR-PF-04, alert within 60 seconds | `incident_event_relay_lag_seconds`; `hazard_report_to_alert_seconds` | The alert is in the report's transaction; relay lag p95 under 2 s |
| NFR-PF-02, position freshness | Age of `responder_last_positions`, p95 | Under 5 s on active missions |
| NFR-PF-05, job progress | `job_progress_age_seconds`, `job_step_duration_seconds` | An update at least every 30 s |
| NFR-RL-04, platform works without AI | `ai_ready` per service next to the core error rate | Core error rate unchanged while `ai_ready` is 0 |
| NFR-RL-02, no upload lost | `upload_incomplete_total` | 0 |
| NFR-PF-06, 200 concurrent users | k6: event streams and read latency | p95 read latency to be agreed |
| Queue health | `job_queue_depth`, `job_queue_oldest_seconds` | Alert above 15 minutes |

- structlog JSON logs carrying `trace_id`, `incident_id` and `job_id`; OpenTelemetry automatic instrumentation for the web, HTTP and database clients.
- Prometheus and Grafana (Grafana is AGPL-3.0; note it in the licence policy). The NVIDIA DCGM exporter only if a GPU exists.

**Security**

- Argon2id password hashing (pwdlib or fastapi-users); short-lived access tokens; rotating refresh tokens in `user_sessions`; a TOTP second factor for Commander and Administrator roles.
- Every request runs `BEGIN; SELECT app.set_session_user($1); …; COMMIT`. Transaction pooling is compatible because the setting is transaction-local; the relay's `LISTEN` uses its own session.
- The citizen one-time code is stored hashed, with attempt counters and rate limits in PostgreSQL. Caddy rate limits in front.
- **An authorisation matrix test** (role × operation × incident participation) in CI. It is the cheapest way to prevent another C4.
- Presigned URLs for one key, five minutes, with a content-length constraint; content-type and magic-byte checks; decompression-bomb limits; EXIF stripping.
- Citizen phone numbers encrypted with `pgcrypto`, or stored as a keyed hash for lookup plus an encrypted column; retention by dropping monthly partitions (NFR-PV-04).
- The audit trail is append-only for every role. Optional stretch: hash-chained rows for tamper evidence.
- Secrets as Docker secrets; gitleaks, Trivy and pip-audit in CI; a software bill of materials per image.
- OWASP ASVS Level 1 mapped before any pilot; the authentication and access-control chapters at Level 2.

**Testing**

| Layer | Tool | What it proves |
|---|---|---|
| Unit | pytest | Formulas, geolocation, cost model, event envelopes |
| Database | pytest + Testcontainers on the project's own image; pgTAP | Invariants I1 to I8; the authorisation matrix; `checks.sql` |
| API | pytest + httpx | OpenAPI contract; idempotency; presigned URL scope |
| End to end | Playwright (web), Maestro (mobile) | The three flows in Section 3.7 |
| Scenario replay | Event log | A recorded incident reproduces the same alerts and routes |
| Resilience | Compose: stop each AI container in turn | The platform stays usable (NFR-RL-04) |
| Load | k6 | 200 concurrent users with live positions and events |

CI runs lint, type checks, unit and database tests, the OpenAPI-to-TypeScript diff gate, a CPU smoke test of each model bundle against a golden tile, and container scanning.

---

## 4. Roadmap

**Assumptions to confirm:** an implementation semester of about 16 weeks; three to four effective builders, because two members hold 23 of 26 commits and the team plan assigns no development work (T1); report duties continue in parallel. Owners below are suggestions based on the commit history, for the team to confirm.

**If implementation starts now, the order matters.** Architect A's proposal reports that "implementation starts tomorrow with AI coding agents" (`gemini_proposal.md:32`). If that is the plan, Phase 0 is not optional, and the schema changes in Section 3.4 should land before any agent writes an endpoint on top of the hazard engine, or the defects in C4 and C5 will be built over.

### Decisions to record before the Project I submission (two weeks)

| Record | Decision | Closes |
|---|---|---|
| ADR-01 | Core backend in Python with FastAPI | P2 |
| ADR-02 | S3 API as the contract; RustFS or SeaweedFS instead of MinIO | C9 |
| ADR-03 | Hazard engine version 2: trigger, definer rights, derived routability, re-routing | C4, C5, C6 |
| ADR-04 | Incident event log with resumable live updates; no Redis | P3, P4 |
| ADR-05 | CPU-first inference; the registry gate; one model per task | C3, C9, A2 |
| ADR-06 | Offline sync protocol outline and the cut list | F4, T4 |

### Phases

| Phase | Weeks | Deliverable | Exit criterion |
|---|---|---|---|
| **0. One working codebase** | 1 to 3 | Recover the package from `3c699f7`; merge or retire V4; notebooks over a versioned wheel; CI skeleton; core Compose with database, objects, API and worker; Alembic baseline; the six decision records; the three-day offline basemap spike | `git clone` then `docker compose up` shows a sign-in page with green health checks; CI builds the database image and passes `checks.sql` on a fresh container |
| **1. One incident, by hand, no AI** | 4 to 7 | Sign-in and the RLS wrapper; incidents, missions and cases; the event log, relay and SSE; the map with a basemap and seeded layers; the mobile app with missions and a snapshot; outbox push and pull for one record type | A Commander and an Analyst manage the seeded incident on the web; a responder sees missions on the phone, updates a case offline and syncs |
| **2. The flagship safety loop** | 8 to 11 | Hazard engine version 2 with invariants I1 to I8; re-routing; push; offline geofence alarm; rejection handling; a scenario replayer; a load test at 200 simulated users | A responder's flood report produces an alert, closed roads, a replaced route and a push within 60 seconds; the offline variant passes; with every AI container stopped, all invariants still pass |
| **3. AI as observers** | 12 to 14 | The serving template; one real model end to end with the registry gate, calibrated sets and the review queue; tile baking | An uploaded image pair produces a damage layer and a review queue on the map within minutes on CPU |
| **4. Harden and rehearse** | 15 to 16 | Reports with frozen snapshots; dashboards; a restore drill; the ASVS Level 1 pass; documentation; the Section 5 corrections | All invariants green in CI; the restore drill recorded; the demonstration script runs twice without failure |

- **MVP:** Phases 0 to 2 plus one real model. That is a coherent, demonstrable, defensible system.
- **Stretch; choose at most two:** the fast lane and on-device detection; photogrammetry and terrain from real imagery; elevation-aware rules; a vision-language second reader; the time-travel replay interface; a Meshtastic relay; similar past cases.
- **Cut, and say so in the report:** Gazebo, ROS 2 and PX4; 3D Gaussian splatting; Kubernetes; Kafka, NATS and Redis; microservices; LitServe, BentoML and Triton; CRDT documents; WebGPU; FAISS; the 7B teacher; a free-text copilot.

### Who does what (suggested)

| Workstream | Suggested owner | Second |
|---|---|---|
| Platform: database, hazard engine, event log, API | Ali, author of the schema and the V4 branch | Mahmoud, author of the requirements and the second ERD |
| Product: web console, mobile app, maps | Mesbah, author of the mapping prototype and the brand | Yassin |
| ML: one model end to end, evaluation, registry | **To be named.** F3 has no owner on the evidence, and Ali already holds two workstreams | Bela, author of the model literature |
| Quality: scenarios, authorisation matrix, end-to-end tests, demonstration script | Joe | Youssef |

### Top risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Bus factor: two people carry the project | High | Name an ML owner now; pair on the database; keep every component small enough to hand over |
| No GPU for development, testing and the demonstration | Certain today | CPU-first design; decide on a rental budget in week 1; state targets for CPU |
| No data for F3 in the target domain | High | Measure recall on a self-annotated Egyptian test set early; report it honestly |
| No drone, so no photogrammetry | Unknown | Ask (Section 6, question 1); keep F2's 3D on public data or cut it |
| Integration time lost to report duties | High | The exit criterion of each phase is a demonstration, not a document |
| Arabic and right-to-left late | Medium | First sprint, with a test |
| AGPL dependencies in a project that declares MIT | Medium | Decide the licence policy (ADR-05) before choosing a detector |

---

## 5. Required changes to the report and plans

Short names in this table: `platform-architecture-plan.md` is `docs/architecture/platform-architecture-plan.md`; `gemini_proposal.md` is `docs/architecture/debate/gemini_proposal.md`; `section_3_3.md` is `docs/documentation/chapter5/section_3_3.md`; "ERD specification" is `docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md`; Section 3.1 and Section 3.2 are the report's own sections.

| Document | Current statement | Proposed change | Reason |
|---|---|---|---|
| `docs/architecture/platform-architecture-plan.md:13` | "Core backend: **NestJS** (TypeScript) modular monolith" | FastAPI in Python | P2 |
| `platform-architecture-plan.md:56,70` | "MinIO (S3 API)" | S3 as the contract; RustFS or SeaweedFS | C9 |
| `platform-architecture-plan.md:80-85` | Job table with `LISTEN/NOTIFY`, "no extra broker" | Queue library, a durable outbox and step resume; say that `NOTIFY` is only a hint | C7, P3 |
| `platform-architecture-plan.md:63-67` | AI services and worker "scale by GPU" | CPU first; name where a GPU would come from | C9 |
| `platform-architecture-plan.md` (whole) | No repository assessment, roadmap or risks | Add the three sections | P1, P6 |
| `platform-architecture-plan.md:159-173` | Blog posts as sources | Primary documentation for each claim | P7 |
| `gemini_proposal.md:96` | "Use `LitServe`" | One FastAPI-based serving template | P5 |
| `gemini_proposal.md:14,224,278` | Redis for fan-out, GPS and one-time codes | Remove | P4 |
| `gemini_proposal.md:277` | MinIO, here and in all 14 companion documents | Replace | C9 |
| `gemini_proposal.md:298-300` | Engine called in the responder's transaction | Trigger with definer rights | C4 |
| `gemini_proposal.md:85,106,122,185` | Unverified numbers and capabilities | Correct or delete | P7 |
| `database/schema/15_security.sql:7`; `database/README.md:69` | "AI / Celery pipeline" | Name the actual queue | Minor |
| `database/schema/12_hazard_engine.sql` | Invoker rights, manual call, per-hazard idempotency, stored previous costs | Version 2 (Section 3.4.3) | C4, C5, D2, D3 |
| `database/schema/07_roads.sql:73` | `AND condition <> 'HAZARD_CLOSED'` | Remove; routability is derived | C5 |
| `database/schema/10_routing.sql:41-50` | `alert_closed_segments` with `prev_*` | Drop `prev_*`; add `routes.supersedes_route_id` | C5, C6 |
| `database/schema/15_security.sql:259,299-312` | Worker role has all rights on all tables | Least privilege; audit trail append-only | C8 |
| `database/schema/04_imagery_ai.sql:66-78`; `01_types.sql:33-34` | Job table without lease, retry or priority | Extend as in Section 3.9 | C7 |
| `database/schema/04_imagery_ai.sql:57-59`; `seed/01_reference_data.sql:113-122` | Nine untrained models marked active | Evidence gate; seeds inactive | C3 |
| `database/schema/08_persons_cases.sql:9-10,18,28,35-37`; `04_imagery_ai.sql:102` | Run-bound tracks; mandatory visibility attributes; every run needs a raster | Relax as in Section 3.5 | C11, D9 |
| `database/build.sh:20` | Drop and recreate as the only schema change | Alembic migrations | D1 |
| `database/seed/02_demo_scenario.sql:294-321`; `database/tests/checks.sql:96-108,299-311` | Alert raised by an owner-run call; tests cover one alert as Analyst | Insert routes before hazards; add the responder path and invariants I1 to I8 | C4, C5 |
| `section_3_3.md:337` | "Third, it is reversible: each closed segment keeps its previous condition and costs, and resolving the alert restores them" | After version 2: routability follows live alerts and the latest observation | C5 |
| `section_3_3.md:196` | "no application role can modify the log (NFR-SC-06)" | Keep the sentence only once the worker role is restricted | C8 |
| `section_3_3.md:301` | "A single flood report from the field leads, within the 60-second target of NFR-PF-04, to a danger zone, closed roads, invalidated routes and warnings" | Keep after the responder path works and is measured; add the replaced route | C4, C6 |
| `section_3_3.md:64,305` | Jobs "can be retried" | Describe lease, retry limit and step resume | C7 |
| `section_3_3.md` Table 3-39 | D-01 to D-10 | Add: D-11 an incident event log with resumable updates; D-12 CPU-first inference and a model activation gate; D-13 an open-source licence policy. Refine D-09 for AGPL components | P3, C3, A3 |
| `section_3_3.md:34,40,108` | "nine domain modules", ten listed, "eight domains" | One count | C12 |
| `section_3_3.md:42`; Section 3.1.5 (not started) | "workers with graphics processors take jobs from the queue" | CPU baseline and optional GPU; list the stack in 3.1.5 | C9 |
| `section_3_3.md:345` | A flooded segment is unusable if the depth is "greater than d(v)" | Unknown depth counts as too deep | Section 3.4.3 |
| ERD specification `:3` | "Target: PostgreSQL 16 + PostGIS 3 + pgRouting 3" next to "implemented … (PostgreSQL 18.7)" | Align with 18 | C12 |
| ERD specification `:27` | "invalidates and recomputes routes passing through the zone" | Implement, or mark as planned until built | C6 |
| ERD specification `:83` | "with optional Postgres Row-Level Security" | Mandatory, per D-04 | C12 |
| ERD specification `:18,21` | Partial-visibility detection and the stationarity rule stated as behaviour | Mark as planned with their data limits | C3, C11, A6 |
| ERD specification `:404` | Offline sync "is a separate design" | Add the protocol outline (Section 3.6) | F4 |
| `README.md`, `docs/api_usage.md`, `docs/PROJECT_ANALYSIS.md`, `docs/model_cards.md`, `docs/dataset_setup.md` | Describe the deleted package as the system | Rewrite, or mark as historical | T2 |
| `docs/PROJECT_ANALYSIS.md:238` | "UAV imagery from Hurricane Florence" | Hurricane Harvey | C12 |
| `docs/claude_view.md:11,15,37-40,213` | "Git is broken"; a real drone; Gazebo as core; 0.74 as "the correct figure" | Correct each | T4, C10 |
| `docs/graduation_project_research_plan.md:312,465` | Gazebo/PX4 as a scope item and a phase | Move to future work | T4 |
| `docs/SAR_Drone_Simulation_Research.md` | AirSim as "TOP RECOMMENDATION"; Streamlit; GPT-4o reports | Mark as background research | T3 |
| `docs/experiments.md` | Eleven experiments "Pending" | Adopt the V4 registry with the official metric | C10 |
| `docs/research_papers.md`; `docs/tier1_papers_summary.md` | DINOv3 described as the backbone in use | Name one backbone per task | A2 |
| `frontend/README.md:20` and the feature READMEs | A missing architecture document; old roles, "victim", "cases", "urgency"; WebSocket as the write path; `/predict` | Rewrite against the database vocabulary | F1 to F5 |
| `AGENTS.md` "Current focus" | Silent on the state of the code | Add a short, dated note on what exists | T5 |
| `docs/team-plan/review/person4_mahmoud.md` M13, M14 | No AI quality targets; no default values | Add the activation gate and calibration targets; propose 10.7 m for downed lines and 15 cm for ordinary vehicles as sourced defaults | D6, C10 |
| Section 3.1.4.4 (not started) | Dependencies do not include power-asset locations | Add the infrastructure inventory as a dependency: the flagship rule cannot fire without asset geometry | Section 6 |
| Chapter 2 related systems (review L1) | None | Use the verified systems in Section 2.2 | — |
| `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.env.example` | A mock-up of two services | Rebuild in Phase 0 | C1, O2 |

---

## 6. Open questions only the team or the owner can answer

1. Is there a drone? Who may fly it, where, and with what permission? This decides whether photogrammetry and 3D exist at all.
2. Will a GPU be rented, with what budget and for how many hours? If not, every performance target must be stated for CPU.
3. Does "every model in its own container" mean nine containers or three model families?
4. Who owns ML after V4? F3 has no owner on the evidence, and one member already holds the database and the ML branches.
5. Is an AGPL-3.0 dependency acceptable, or must the detector be under a permissive licence?
6. Can a utility or a civil-defence contact confirm the rule distances and the vehicle depth limits?
7. Can any real data be obtained (power assets, incident records), or is the whole scenario synthetic?
8. How long is the implementation semester, and which members are assigned to build rather than to write?

---

## Sources

### A. Read or queried in this session

| # | Source | How it was checked | Used for |
|---|---|---|---|
| A1 | PostgreSQL, `NOTIFY` — https://www.postgresql.org/docs/current/sql-notify.html | fetched | Payload under 8,000 bytes; delivery at commit (P3) |
| A2 | PostgreSQL, `LISTEN` — https://www.postgresql.org/docs/current/sql-listen.html | not re-fetched | Notifications are not kept for absent listeners (P3) |
| A3 | PostgREST configuration reference — https://docs.postgrest.org/en/latest/references/configuration.html | fetched | `db-pre-request`, `db-root-spec` (Section 2.3) |
| A4 | FloodNet, Rahnemoonfar et al. — https://arxiv.org/abs/2012.02951 | abstract fetched | "captured after the hurricane Harvey" (C12) |
| A5 | SeaDronesSee, Varga et al., WACV 2022 — https://arxiv.org/abs/2105.01922 | search; counts unverified | Classes and size (C11, Section 2.5) |
| A6 | SARD dataset, IEEE DataPort | search; count of 1,981 images unverified | Size (C11) |
| A7 | xView2 scoring code — https://github.com/DIUx-xView/xView2_scoring | ran (`xview2_metrics.py`) | Official metric (C10) |
| A8 | xView2 baseline — https://github.com/DIUx-xView/xView2_baseline | API | Reference implementation |
| A9 | Electrical Safety Foundation International, downed power lines — https://www.esfi.org/downed-power-lines | search | 35 feet (D6) |
| A10 | US National Weather Service, Turn Around Don't Drown — https://www.weather.gov/tsa/hydro_tadd | search | 6, 12 and 24 inches (Section 2.5) |
| A11 | MinIO repository README — https://github.com/minio/minio | ran | "NO LONGER MAINTAINED" (C9) |
| A12 | Ultralytics README — https://github.com/ultralytics/ultralytics | ran | AGPL-3.0 and the enterprise licence line; YOLO26 (A2, A3) |
| A13 | Microsoft Global ML Building Footprints — https://github.com/microsoft/GlobalMLBuildingFootprints | API; size and Africa coverage from search, unverified by me | Skip building segmentation |
| A14 | RescueNet dataset repository — https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation | API (MIT, last push 2024-05-17) | Post-disaster road labels |

### B. Referred to in the repository or by the proposals; not re-fetched here

| # | Source | Note |
|---|---|---|
| B1 | xBD, Gupta et al. — https://arxiv.org/abs/1911.09296 | Cited in the repository's own research plan |
| B2 | DINOv3, Siméoni et al. — https://arxiv.org/abs/2508.10104 | Cited as rank 4 in `docs/research_papers.md` |
| B3 | Angelopoulos and Bates, *A Gentle Introduction to Conformal Prediction* — https://arxiv.org/abs/2107.07511 | Method behind Section 3.5; check the identifier before citing |
| B4 | Kleppmann et al., *Local-first software* — https://arxiv.org/abs/1901.01908; Ink & Switch essay — https://www.inkandswitch.com/local-first/ | Background for the sync design; check before citing |
| B5 | Fowler, *MonolithFirst* — https://martinfowler.com/bliki/MonolithFirst.html | Cited by both proposals |
| B6 | React Native blog, *Use a framework to build React Native apps* — https://reactnative.dev/blog/2024/06/25/use-a-framework-to-build-react-native-apps | Cited by the platform plan for Expo |
| B7 | OpenStreetMap terrain tiles on the AWS Open Data Registry — https://registry.opendata.aws/terrain-tiles/ | Candidate terrain source for MapLibre |
| B8 | OpenDroneMap documentation — https://docs.opendronemap.org/ | Cited in the research plan |

### C. Repositories checked through the GitHub API on 25 November 2026

Each exists with the status shown in Section 2.3, unless marked.

- **Reference systems:** https://github.com/sahana/eden · https://github.com/ushahidi/platform · https://github.com/kobotoolbox/kpi · https://github.com/IFRCGo/go-api · https://github.com/google/personfinder (archived) · https://github.com/hotosm/fAIr · https://github.com/hotosm/tasking-manager · https://github.com/microsoft/building-damage-assessment · https://github.com/gem/oq-engine · https://github.com/OCHA-DAP/ds-geospatial-impact-estimates (1 star, no licence)
- **Architecture references:** https://github.com/kgrzybek/modular-monolith-with-ddd · https://github.com/GoogleCloudPlatform/microservices-demo · https://github.com/dotnet/eShop
- **Backend:** https://github.com/fastapi/fastapi · https://github.com/sqlalchemy/sqlalchemy · https://github.com/sqlalchemy/alembic · https://github.com/psycopg/psycopg · https://github.com/encode/httpx · https://github.com/astral-sh/uv · https://github.com/astral-sh/ruff · https://github.com/PostgREST/postgrest · https://github.com/nestjs/nest
- **Queues and streaming:** https://github.com/procrastinate-org/procrastinate · https://github.com/janbjorge/pgqueuer · https://github.com/pgmq/pgmq · https://github.com/dbos-inc/dbos-transact-py · https://github.com/hatchet-dev/hatchet · https://github.com/redis/redis · https://github.com/apache/kafka · https://github.com/nats-io/nats-server · https://github.com/emqx/emqx
- **Serving:** https://github.com/Lightning-AI/LitServe · https://github.com/bentoml/BentoML · https://github.com/triton-inference-server/server · https://github.com/pytorch/serve (archived) · https://github.com/vllm-project/vllm · https://github.com/openvinotoolkit/openvino · https://github.com/pytorch/executorch
- **Machine learning:** https://github.com/microsoft/torchgeo · https://github.com/facebookresearch/dinov3 · https://github.com/lyuwenyu/RT-DETR · https://github.com/roboflow/rf-detr · https://github.com/Megvii-BaseDetection/YOLOX · https://github.com/Peterande/D-FINE · https://github.com/obss/sahi · https://github.com/FoundationVision/ByteTrack · https://github.com/mlflow/mlflow · https://github.com/iterative/dvc · https://github.com/scikit-learn-contrib/MAPIE · https://github.com/Lightning-AI/torchmetrics · https://github.com/NVIDIA/dcgm-exporter
- **Geospatial:** https://github.com/maplibre/martin · https://github.com/developmentseed/titiler · https://github.com/protomaps/PMTiles · https://github.com/felt/tippecanoe · https://github.com/stac-utils/pgstac · https://github.com/stac-utils/pystac-client · https://github.com/stac-utils/stac-fastapi · https://github.com/hyperknot/openfreemap · https://github.com/maplibre/maplibre-gl-js · https://github.com/maplibre/maplibre-react-native · https://github.com/maplibre/maplibre-gl-native · https://github.com/CesiumGS/cesium · https://github.com/OpenDroneMap/ODM · https://github.com/OpenDroneMap/NodeODM · https://github.com/pgRouting/pgRouting · https://github.com/pgRouting/osm2pgrouting · https://github.com/valhalla/valhalla · https://github.com/postgis/docker-postgis · https://github.com/pgvector/pgvector
- **Storage:** https://github.com/rustfs/rustfs · https://github.com/seaweedfs/seaweedfs · https://github.com/versity/versitygw
- **Offline and mobile:** https://github.com/powersync-ja/powersync-js · https://github.com/powersync-ja/powersync-service · https://github.com/op-engineering/op-sqlite · https://github.com/electric-sql/electric · https://github.com/electric-sql/pglite · https://github.com/tinyplex/tinybase · https://github.com/automerge/automerge · https://github.com/expo/expo · https://github.com/mobile-dev-inc/maestro · https://github.com/meshtastic/firmware · https://github.com/servalproject/batphone (last push 2018)
- **Quality, security, operations:** https://github.com/fastapi-users/fastapi-users · https://github.com/frankie567/pwdlib · https://github.com/pytest-dev/pytest · https://github.com/testcontainers/testcontainers-python · https://github.com/theory/pgtap · https://github.com/aquasecurity/trivy · https://github.com/pypa/pip-audit · https://github.com/gitleaks/gitleaks · https://github.com/caddyserver/caddy · https://github.com/open-telemetry/opentelemetry-python · https://github.com/hynek/structlog · https://github.com/prometheus/prometheus · https://github.com/grafana/grafana · https://github.com/pgbackrest/pgbackrest · https://github.com/wal-g/wal-g · https://github.com/Kozea/WeasyPrint · https://github.com/TanStack/router · https://github.com/TanStack/query
- **Simulators:** https://github.com/microsoft/AirSim (not archived; last release 2022)

Docker Hub tags for `postgis/postgis` and `pgvector/pgvector` were read from the Docker Hub API on the same date.

### What this review could not check

- **The database was not run.** Every SQL finding marked "static" comes from reading the files. The reproduction snippets are written to be pasted into `psql` against the demo database and rolled back.
- **No Python was executed against the project.** The claim that imports fail rests on the absence of the package and a single `ModuleNotFoundError` check.
- **Chapters 1, 2 and 5 and Sections 3.1 and 3.2** were not opened in Word. They are known here through the team's review files and through Section 3.3's references to them.
- **`outputs/` is absent from this checkout,** so the recorded V4 numbers are quoted from the branch's own documents, not from the artifacts.
- **Architect A's 14 companion documents were not read.** Statements that something is absent from that proposal rest on a keyword search of them.
- **Star counts and release numbers** are as returned by the API on 25 November 2026 and will drift.
- **Web figures marked "search"** came from search summaries; the two guidance pages (ESFI, NWS) and the dataset counts should be opened once before being cited in the report.
