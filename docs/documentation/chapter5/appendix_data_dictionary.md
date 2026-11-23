# Appendix: Data Dictionary

Generated from the PostgreSQL catalog of the implemented schema (`database/schema`). Tables are grouped by the information domains of Section 3.3.3. Null = whether the column accepts NULL; PK primary key, UQ unique, FK foreign key with its target table.

## Identity and Access

### agencies

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| name | text | no |  | UQ |
| agency_type | agency_type | no |  |  |
| parent_agency_id | uuid | yes |  | FK → agencies |
| jurisdiction | geometry(MultiPolygon,4326) | yes |  |  |
| phone | text | yes |  |  |
| is_active | boolean | no | `true` |  |
| created_at | timestamp with time zone | no | `now()` |  |
| updated_at | timestamp with time zone | no | `now()` |  |

### roles

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| code | text | no |  | PK |
| name | text | no |  |  |
| scope | role_scope | no |  |  |

### permissions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| code | text | no |  | PK |
| description | text | no |  |  |

### role_permissions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| role_code | text | no |  | FK → roles, PK |
| permission_code | text | no |  | FK → permissions, PK |

### users

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| agency_id | uuid | yes |  | FK → agencies |
| role_code | text | no |  | FK → roles |
| full_name | text | no |  |  |
| email | citext | no |  | UQ |
| phone | text | yes |  |  |
| password_hash | text | no |  |  |
| job_title | text | yes |  |  |
| badge_number | text | yes |  |  |
| status | user_status | no | `'INVITED'::user_status` |  |
| last_login_at | timestamp with time zone | yes |  |  |
| created_at | timestamp with time zone | no | `now()` |  |
| updated_at | timestamp with time zone | no | `now()` |  |
| deleted_at | timestamp with time zone | yes |  |  |

### user_sessions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| user_id | uuid | no |  | FK → users |
| refresh_token_hash | text | no |  | UQ |
| device_info | text | yes |  |  |
| created_at | timestamp with time zone | no | `now()` |  |
| expires_at | timestamp with time zone | no |  |  |
| revoked_at | timestamp with time zone | yes |  |  |

### user_devices

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| user_id | uuid | no |  | FK → users |
| platform | device_platform | no |  |  |
| push_token | text | no |  | UQ |
| last_seen_at | timestamp with time zone | no | `now()` |  |

### teams

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| agency_id | uuid | no |  | FK → agencies, UQ |
| name | text | no |  | UQ |
| team_type | team_type | no |  |  |
| home_base | geometry(Point,4326) | yes |  |  |
| status | team_status | no | `'AVAILABLE'::team_status` |  |
| created_at | timestamp with time zone | no | `now()` |  |

### team_members

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| team_id | uuid | no |  | FK → teams |
| user_id | uuid | no |  | FK → users |
| is_leader | boolean | no | `false` |  |
| joined_at | timestamp with time zone | no | `now()` |  |
| left_at | timestamp with time zone | yes |  |  |

### vehicles

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| agency_id | uuid | no |  | FK → agencies, UQ |
| team_id | uuid | yes |  | FK → teams |
| call_sign | text | no |  | UQ |
| vehicle_type | vehicle_type | no |  |  |
| plate_number | text | yes |  |  |
| max_water_depth_cm | integer | yes |  |  |
| status | vehicle_status | no | `'AVAILABLE'::vehicle_status` |  |

## Incidents and Operations

### incidents

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| code | text | no |  | UQ |
| name | text | no |  |  |
| disaster_type | disaster_type | no |  |  |
| status | incident_status | no | `'ACTIVE'::incident_status` |  |
| severity | smallint | no |  |  |
| lead_agency_id | uuid | no |  | FK → agencies |
| area | geometry(MultiPolygon,4326) | no |  |  |
| is_historical | boolean | no | `false` |  |
| started_at | timestamp with time zone | no | `now()` |  |
| closed_at | timestamp with time zone | yes |  |  |
| created_by | uuid | yes |  | FK → users |
| created_at | timestamp with time zone | no | `now()` |  |
| updated_at | timestamp with time zone | no | `now()` |  |

### incident_agencies

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| incident_id | uuid | no |  | FK → incidents, PK |
| agency_id | uuid | no |  | FK → agencies, PK |
| participation | participation_role | no | `'SUPPORT'::participation_role` |  |
| status | participation_status | no | `'INVITED'::participation_status` |  |
| invited_by | uuid | yes |  | FK → users |
| invited_at | timestamp with time zone | no | `now()` |  |
| joined_at | timestamp with time zone | yes |  |  |

### zones

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| name | text | no |  |  |
| zone_type | zone_type | no |  |  |
| geom | geometry(Geometry,4326) | no |  |  |
| created_by | uuid | yes |  | FK → users |
| created_at | timestamp with time zone | no | `now()` |  |

### missions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents, UQ |
| agency_id | uuid | no |  | FK → agencies |
| code | text | no |  | UQ |
| title | text | no |  |  |
| mission_type | mission_type | no |  |  |
| priority | smallint | no | `3` |  |
| status | mission_status | no | `'PLANNED'::mission_status` |  |
| target_zone_id | uuid | yes |  | FK → zones |
| target_geom | geometry(Geometry,4326) | yes |  |  |
| created_by | uuid | yes |  | FK → users |
| created_at | timestamp with time zone | no | `now()` |  |
| updated_at | timestamp with time zone | no | `now()` |  |
| started_at | timestamp with time zone | yes |  |  |
| completed_at | timestamp with time zone | yes |  |  |

### mission_assignments

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| mission_id | uuid | no |  | FK → missions |
| team_id | uuid | yes |  | FK → teams |
| user_id | uuid | yes |  | FK → users |
| vehicle_id | uuid | yes |  | FK → vehicles |
| assigned_by | uuid | yes |  | FK → users |
| assigned_at | timestamp with time zone | no | `now()` |  |
| released_at | timestamp with time zone | yes |  |  |
| response | assignment_response | no | `'PENDING'::assignment_response` |  |

### mission_status_history

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| mission_id | uuid | no |  | FK → missions |
| from_status | mission_status | yes |  |  |
| to_status | mission_status | no |  |  |
| changed_by | uuid | yes |  | FK → users |
| changed_at | timestamp with time zone | no | `now()` |  |
| note | text | yes |  |  |

## Imagery and Analysis Pipeline

### capture_sessions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| mission_id | uuid | yes |  | FK → missions |
| source_type | capture_source | no |  |  |
| phase | capture_phase | no |  |  |
| provider | text | yes |  |  |
| captured_from | timestamp with time zone | yes |  |  |
| captured_to | timestamp with time zone | yes |  |  |
| coverage | geometry(Polygon,4326) | yes |  |  |
| uploaded_by | uuid | yes |  | FK → users |
| status | session_status | no | `'UPLOADING'::session_status` |  |
| created_at | timestamp with time zone | no | `now()` |  |

### images

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| session_id | uuid | no |  | FK → capture_sessions |
| media_kind | media_kind | no | `'PHOTO'::media_kind` |  |
| frame_index | integer | yes |  |  |
| storage_key | text | no |  |  |
| sha256 | text | no |  | UQ |
| width_px | integer | no |  |  |
| height_px | integer | no |  |  |
| spectral_band | spectral_band | no | `'RGB'::spectral_band` |  |
| captured_at | timestamp with time zone | yes |  |  |
| camera_position | geometry(PointZ,4326) | yes |  |  |
| altitude_agl_m | numeric(7,2) | yes |  |  |
| gimbal_pitch | numeric(6,2) | yes |  |  |
| gimbal_yaw | numeric(6,2) | yes |  |  |
| gimbal_roll | numeric(6,2) | yes |  |  |
| gsd_cm | numeric(7,2) | yes |  |  |
| gps_accuracy_m | numeric(7,2) | yes |  |  |
| footprint | geometry(Polygon,4326) | yes |  |  |
| exif | jsonb | yes |  |  |

### raster_products

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| session_id | uuid | no |  | FK → capture_sessions |
| produced_by_run_id | uuid | yes |  | FK → inference_runs |
| product_type | raster_type | no |  |  |
| storage_key | text | no |  |  |
| resolution_m | numeric(8,3) | yes |  |  |
| bounds | geometry(Polygon,4326) | no |  |  |
| created_at | timestamp with time zone | no | `now()` |  |

### ai_models

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| name | text | no |  | UQ |
| version | text | no |  | UQ |
| task | model_task | no |  |  |
| architecture | text | no |  |  |
| training_datasets | text[] | no | `'{}'::text[]` |  |
| metrics | jsonb | yes |  |  |
| weights_uri | text | yes |  |  |
| is_active | boolean | no | `false` |  |
| created_at | timestamp with time zone | no | `now()` |  |

### processing_jobs

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| session_id | uuid | yes |  | FK → capture_sessions |
| job_type | job_type | no |  |  |
| status | job_status | no | `'QUEUED'::job_status` |  |
| progress_pct | smallint | no | `0` |  |
| error_message | text | yes |  |  |
| requested_by | uuid | yes |  | FK → users |
| queued_at | timestamp with time zone | no | `now()` |  |
| started_at | timestamp with time zone | yes |  |  |
| finished_at | timestamp with time zone | yes |  |  |

### inference_runs

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| job_id | uuid | no |  | FK → processing_jobs |
| model_id | uuid | no |  | FK → ai_models |
| pre_raster_id | uuid | yes |  | FK → raster_products |
| post_raster_id | uuid | no |  | FK → raster_products |
| params | jsonb | no | `'{}'::jsonb` |  |
| status | job_status | no | `'QUEUED'::job_status` |  |
| started_at | timestamp with time zone | yes |  |  |
| finished_at | timestamp with time zone | yes |  |  |

## F1 Buildings and Cost

### buildings

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents, UQ |
| external_ref | text | yes |  | UQ |
| footprint | geometry(Polygon,4326) | no |  |  |
| area_m2 | numeric | yes | `st_area((footprint)::geography)` |  |
| floors | smallint | yes |  |  |
| height_m | numeric(6,2) | yes |  |  |
| occupancy | occupancy_type | no | `'UNKNOWN'::occupancy_type` |  |
| construction | construction_type | no | `'UNKNOWN'::construction_type` |  |
| est_occupants | integer | yes |  |  |
| address | text | yes |  |  |
| source | building_source | no |  |  |
| created_at | timestamp with time zone | no | `now()` |  |

### building_assessments

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| building_id | uuid | no |  | FK → buildings |
| inference_run_id | uuid | yes |  | FK → inference_runs |
| assessed_by | uuid | yes |  | FK → users |
| method | assessment_method | no |  |  |
| damage_grade | damage_grade | no |  |  |
| p_no_damage | numeric(4,3) | yes |  |  |
| p_minor | numeric(4,3) | yes |  |  |
| p_major | numeric(4,3) | yes |  |  |
| p_destroyed | numeric(4,3) | yes |  |  |
| pre_image_id | uuid | yes |  | FK → images |
| post_image_id | uuid | yes |  | FK → images |
| review_status | review_status | no | `'PENDING'::review_status` |  |
| reviewed_by | uuid | yes |  | FK → users |
| reviewed_at | timestamp with time zone | yes |  |  |
| is_current | boolean | no | `true` |  |
| created_at | timestamp with time zone | no | `now()` |  |

### cost_profiles

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| name | text | no |  | UQ |
| region | text | no |  |  |
| currency | character(3) | no |  |  |
| source | text | no |  |  |
| valid_from | date | no |  |  |

### cost_profile_unit_rates

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| profile_id | uuid | no |  | FK → cost_profiles, PK |
| occupancy | occupancy_type | no |  | PK |
| construction | construction_type | no |  | PK |
| cost_per_m2_low | numeric(12,2) | no |  |  |
| cost_per_m2_high | numeric(12,2) | no |  |  |

### cost_profile_repair_ratios

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| profile_id | uuid | no |  | FK → cost_profiles, PK |
| damage_grade | damage_grade | no |  | PK |
| ratio_low | numeric(4,3) | no |  |  |
| ratio_high | numeric(4,3) | no |  |  |

### cost_estimates

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| building_id | uuid | no |  | FK → buildings |
| assessment_id | uuid | no |  | FK → building_assessments |
| cost_profile_id | uuid | no |  | FK → cost_profiles |
| floor_area_m2 | numeric(12,2) | no |  |  |
| repair_ratio_low | numeric(4,3) | no |  |  |
| repair_ratio_high | numeric(4,3) | no |  |  |
| cost_low | numeric(14,2) | no |  |  |
| cost_high | numeric(14,2) | no |  |  |
| currency | character(3) | no |  |  |
| assumptions | jsonb | no | `'{}'::jsonb` |  |
| computed_at | timestamp with time zone | no | `now()` |  |

## F2 Roads and Routing

### road_nodes

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| incident_id | uuid | no |  | FK → incidents |
| geom | geometry(Point,4326) | no |  |  |

### road_segments

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| incident_id | uuid | no |  | FK → incidents |
| osm_way_id | bigint | yes |  |  |
| source | bigint | no |  | FK → road_nodes |
| target | bigint | no |  | FK → road_nodes |
| geom | geometry(LineString,4326) | no |  |  |
| name | text | yes |  |  |
| road_class | road_class | no | `'RESIDENTIAL'::road_class` |  |
| width_m | numeric(5,2) | yes |  |  |
| is_bridge | boolean | no | `false` |  |
| oneway | boolean | no | `false` |  |
| length_m | numeric(10,2) | no |  |  |
| base_travel_s | numeric(10,2) | no |  |  |
| condition | road_condition | no | `'UNKNOWN'::road_condition` |  |
| water_depth_cm | integer | yes |  |  |
| condition_confidence | numeric(4,3) | yes |  |  |
| condition_updated_at | timestamp with time zone | yes |  |  |
| cost | double precision | no |  |  |
| reverse_cost | double precision | no |  |  |

### road_condition_observations

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| segment_id | bigint | no |  | FK → road_segments |
| condition | road_condition | no |  |  |
| water_depth_cm | integer | yes |  |  |
| confidence | numeric(4,3) | yes |  |  |
| inference_run_id | uuid | yes |  | FK → inference_runs |
| reported_by | uuid | yes |  | FK → users |
| citizen_request_id | uuid | yes |  | FK → citizen_requests |
| observed_at | timestamp with time zone | no | `now()` |  |

### routes

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| mission_id | uuid | yes |  | FK → missions |
| requested_by | uuid | yes |  | FK → users |
| vehicle_type | vehicle_type | no |  |  |
| origin | geometry(Point,4326) | no |  |  |
| destination | geometry(Point,4326) | no |  |  |
| destination_case_id | uuid | yes |  | FK → assistance_cases |
| destination_facility_id | uuid | yes |  | FK → facilities |
| algorithm | route_algorithm | no | `'ASTAR'::route_algorithm` |  |
| rank | smallint | no | `1` |  |
| geom | geometry(LineString,4326) | no |  |  |
| length_m | numeric(10,2) | no |  |  |
| est_travel_s | numeric(10,2) | no |  |  |
| risk_score | numeric(6,3) | no | `0` |  |
| status | route_status | no | `'ACTIVE'::route_status` |  |
| invalidated_by_alert_id | uuid | yes |  | FK → compound_alerts |
| computed_at | timestamp with time zone | no | `now()` |  |

### route_segments

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| route_id | uuid | no |  | FK → routes, PK |
| seq | integer | no |  | PK |
| segment_id | bigint | no |  | FK → road_segments |

### alert_closed_segments

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| alert_id | uuid | no |  | FK → compound_alerts, PK |
| segment_id | bigint | no |  | FK → road_segments, PK |
| prev_condition | road_condition | no |  |  |
| prev_cost | double precision | no |  |  |
| prev_reverse_cost | double precision | no |  |  |
| closed_at | timestamp with time zone | no | `now()` |  |

## F3/F4 Persons and Cases

### person_tracks

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| inference_run_id | uuid | no |  | FK → inference_runs, UQ |
| tracker_local_id | integer | no |  | UQ |
| first_seen_at | timestamp with time zone | no |  |  |
| last_seen_at | timestamp with time zone | no |  |  |
| last_position | geometry(Point,4326) | no |  |  |
| last_position_error_m | numeric(7,2) | yes |  |  |
| movement_state | movement_state | no | `'UNKNOWN'::movement_state` |  |
| max_confidence | numeric(4,3) | yes |  |  |
| detection_count | integer | no | `0` |  |

### person_detections

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| incident_id | uuid | no |  | FK → incidents |
| inference_run_id | uuid | no |  | FK → inference_runs |
| image_id | uuid | no |  | FK → images |
| track_id | uuid | yes |  | FK → person_tracks |
| bbox_x | integer | no |  |  |
| bbox_y | integer | no |  |  |
| bbox_w | integer | no |  |  |
| bbox_h | integer | no |  |  |
| confidence | numeric(4,3) | no |  |  |
| visibility | visibility_level | no |  |  |
| occlusion_ratio | numeric(3,2) | yes |  |  |
| posture | posture | no | `'UNKNOWN'::posture` |  |
| location | geometry(Point,4326) | no |  |  |
| location_error_m | numeric(7,2) | no |  |  |
| detected_at | timestamp with time zone | no |  |  |

### facilities

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| agency_id | uuid | yes |  | FK → agencies |
| name | text | no |  |  |
| facility_type | facility_type | no |  |  |
| geom | geometry(Point,4326) | no |  |  |
| capacity_total | integer | yes |  |  |
| capacity_available | integer | yes |  |  |
| updated_at | timestamp with time zone | no | `now()` |  |

### assistance_cases

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents, UQ |
| code | text | no |  | UQ |
| source | case_source | no |  |  |
| track_id | uuid | yes |  | FK → person_tracks |
| citizen_request_id | uuid | yes |  | FK → citizen_requests |
| reported_by | uuid | yes |  | FK → users |
| location | geometry(Point,4326) | no |  |  |
| location_error_m | numeric(7,2) | yes |  |  |
| building_id | uuid | yes |  | FK → buildings |
| people_count | smallint | no | `1` |  |
| triage | triage_category | no | `'UNTRIAGED'::triage_category` |  |
| status | case_status | no | `'DETECTED'::case_status` |  |
| priority_score | numeric(6,2) | no | `0` |  |
| assigned_mission_id | uuid | yes |  | FK → missions |
| transported_to_facility_id | uuid | yes |  | FK → facilities |
| verified_by | uuid | yes |  | FK → users |
| verified_at | timestamp with time zone | yes |  |  |
| created_at | timestamp with time zone | no | `now()` |  |
| updated_at | timestamp with time zone | no | `now()` |  |
| closed_at | timestamp with time zone | yes |  |  |

### case_events

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| case_id | uuid | no |  | FK → assistance_cases |
| event_type | case_event_type | no |  |  |
| from_status | case_status | yes |  |  |
| to_status | case_status | yes |  |  |
| triage | triage_category | yes |  |  |
| note | text | yes |  |  |
| media_id | uuid | yes |  | FK → media_files |
| actor_id | uuid | yes |  | FK → users |
| created_at | timestamp with time zone | no | `now()` |  |

## F5 Hazards and Alerts

### infrastructure_assets

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| asset_type | asset_type | no |  |  |
| geom | geometry(Geometry,4326) | no |  |  |
| voltage_kv | numeric(7,2) | yes |  |  |
| operator | text | yes |  |  |
| power_state | power_state | no | `'UNKNOWN'::power_state` |  |
| state_updated_at | timestamp with time zone | yes |  |  |

### hazards

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| hazard_type | hazard_type | no |  |  |
| geom | geometry(Geometry,4326) | no |  |  |
| severity | smallint | no |  |  |
| confidence | numeric(4,3) | yes |  |  |
| origin | hazard_origin | no |  |  |
| inference_run_id | uuid | yes |  | FK → inference_runs |
| reported_by | uuid | yes |  | FK → users |
| citizen_request_id | uuid | yes |  | FK → citizen_requests |
| status | hazard_status | no | `'SUSPECTED'::hazard_status` |  |
| attributes | jsonb | no | `'{}'::jsonb` |  |
| observed_at | timestamp with time zone | no | `now()` |  |
| expires_at | timestamp with time zone | yes |  |  |

### hazard_rules

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| code | text | no |  | UQ |
| name | text | no |  |  |
| description | text | no |  |  |
| primary_hazard_type | hazard_type | no |  |  |
| secondary_kind | rule_operand | no |  |  |
| secondary_types | text[] | no |  |  |
| max_distance_m | numeric(7,2) | no |  |  |
| danger_buffer_m | numeric(7,2) | no |  |  |
| resulting_severity | smallint | no |  |  |
| closes_roads | boolean | no | `true` |  |
| warning_template | text | no |  |  |
| is_active | boolean | no | `true` |  |

### compound_alerts

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| rule_id | uuid | no |  | FK → hazard_rules |
| title | text | no |  |  |
| danger_zone | geometry(MultiPolygon,4326) | no |  |  |
| severity | smallint | no |  |  |
| status | alert_status | no | `'ACTIVE'::alert_status` |  |
| triggered_at | timestamp with time zone | no | `now()` |  |
| acknowledged_by | uuid | yes |  | FK → users |
| acknowledged_at | timestamp with time zone | yes |  |  |
| resolved_by | uuid | yes |  | FK → users |
| resolved_at | timestamp with time zone | yes |  |  |
| resolution_note | text | yes |  |  |

### compound_alert_sources

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| alert_id | uuid | no |  | FK → compound_alerts |
| hazard_id | uuid | yes |  | FK → hazards |
| asset_id | uuid | yes |  | FK → infrastructure_assets |

## Field Operations and Notifications

### responder_positions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| user_id | uuid | no |  | FK → users |
| incident_id | uuid | yes |  | FK → incidents |
| mission_id | uuid | yes |  | FK → missions |
| recorded_at | timestamp with time zone | no |  | PK |
| geom | geometry(Point,4326) | no |  |  |
| accuracy_m | numeric(7,2) | no |  |  |
| speed_mps | numeric(6,2) | yes |  |  |
| heading_deg | numeric(5,2) | yes |  |  |
| battery_pct | smallint | yes |  |  |

### responder_last_positions

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| user_id | uuid | no |  | FK → users, PK |
| geom | geometry(Point,4326) | no |  |  |
| accuracy_m | numeric(7,2) | no |  |  |
| recorded_at | timestamp with time zone | no |  |  |
| incident_id | uuid | yes |  | FK → incidents |
| mission_id | uuid | yes |  | FK → missions |

### sos_alerts

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| user_id | uuid | no |  | FK → users |
| location | geometry(Point,4326) | no |  |  |
| message | text | yes |  |  |
| media_id | uuid | yes |  | FK → media_files |
| status | sos_status | no | `'TRIGGERED'::sos_status` |  |
| triggered_at | timestamp with time zone | no | `now()` |  |
| acknowledged_by | uuid | yes |  | FK → users |
| acknowledged_at | timestamp with time zone | yes |  |  |
| resolved_at | timestamp with time zone | yes |  |  |

### notifications

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| user_id | uuid | no |  | FK → users |
| incident_id | uuid | yes |  | FK → incidents |
| kind | notification_kind | no |  |  |
| title | text | no |  |  |
| body | text | no |  |  |
| severity | smallint | no | `3` |  |
| alert_id | uuid | yes |  | FK → compound_alerts |
| mission_id | uuid | yes |  | FK → missions |
| case_id | uuid | yes |  | FK → assistance_cases |
| sos_id | uuid | yes |  | FK → sos_alerts |
| route_id | uuid | yes |  | FK → routes |
| created_at | timestamp with time zone | no | `now()` |  |
| delivered_at | timestamp with time zone | yes |  |  |
| read_at | timestamp with time zone | yes |  |  |

## Citizens, Reports and Audit

### citizens

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| phone | text | no |  | UQ |
| full_name | text | yes |  |  |
| preferred_language | text | no | `'ar'::text` |  |
| phone_verified_at | timestamp with time zone | yes |  |  |
| is_blocked | boolean | no | `false` |  |
| created_at | timestamp with time zone | no | `now()` |  |

### citizen_requests

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| citizen_id | uuid | no |  | FK → citizens |
| incident_id | uuid | yes |  | FK → incidents |
| request_type | citizen_request_type | no |  |  |
| location | geometry(Point,4326) | no |  |  |
| location_accuracy_m | numeric(7,2) | yes |  |  |
| people_count | smallint | yes |  |  |
| description | text | yes |  |  |
| status | citizen_request_status | no | `'RECEIVED'::citizen_request_status` |  |
| duplicate_of_id | uuid | yes |  | FK → citizen_requests |
| verified_by | uuid | yes |  | FK → users |
| verified_at | timestamp with time zone | yes |  |  |
| created_at | timestamp with time zone | no | `now()` |  |

### media_files

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| storage_key | text | no |  |  |
| mime_type | text | no |  |  |
| sha256 | text | no |  |  |
| uploaded_by_user | uuid | yes |  | FK → users |
| uploaded_by_citizen | uuid | yes |  | FK → citizens |
| created_at | timestamp with time zone | no | `now()` |  |

### citizen_request_media

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| request_id | uuid | no |  | FK → citizen_requests, PK |
| media_id | uuid | no |  | FK → media_files, PK |

### reports

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| incident_id | uuid | no |  | FK → incidents |
| report_type | report_type | no |  |  |
| title | text | no |  |  |
| period_from | timestamp with time zone | yes |  |  |
| period_to | timestamp with time zone | yes |  |  |
| scope_zone_id | uuid | yes |  | FK → zones |
| status | report_status | no | `'DRAFT'::report_status` |  |
| stats_snapshot | jsonb | no | `'{}'::jsonb` |  |
| pdf_storage_key | text | yes |  |  |
| html_storage_key | text | yes |  |  |
| job_id | uuid | yes |  | FK → processing_jobs |
| generated_by | uuid | yes |  | FK → users |
| approved_by | uuid | yes |  | FK → users |
| approved_at | timestamp with time zone | yes |  |  |
| created_at | timestamp with time zone | no | `now()` |  |
| disclaimer | text | no | `'AI decision-support output; human review required.'::text` |  |

### report_shares

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| report_id | uuid | no |  | FK → reports, PK |
| agency_id | uuid | no |  | FK → agencies, PK |
| shared_by | uuid | yes |  | FK → users |
| shared_at | timestamp with time zone | no | `now()` |  |

### image_embeddings

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | uuid | no | `uuidv7()` | PK |
| model_id | uuid | no |  | FK → ai_models |
| incident_id | uuid | no |  | FK → incidents |
| source_kind | embedding_source | no |  |  |
| building_id | uuid | yes |  | FK → buildings |
| image_id | uuid | yes |  | FK → images |
| embedding | vector(768) | no |  |  |
| created_at | timestamp with time zone | no | `now()` |  |

### audit_log

| Column | Type | Null | Default | Key |
|---|---|---|---|---|
| id | bigint | no |  | PK |
| actor_user_id | uuid | yes |  |  |
| action | text | no |  |  |
| entity_table | text | no |  |  |
| entity_id | text | yes |  |  |
| before | jsonb | yes |  |  |
| after | jsonb | yes |  |  |
| ip | inet | yes |  |  |
| created_at | timestamp with time zone | no | `now()` | PK |

