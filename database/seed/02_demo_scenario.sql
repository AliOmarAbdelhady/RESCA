-- Demo scenario: "Downtown Cairo Earthquake & Flash Flood" (fictional data)
-- Shows every feature end to end on a small 4×4 street grid:
--   F1 buildings + damage + cost · F2 road graph + route · F3/F4 detections,
--   track, assistance case · F5 floodwater next to a live power line → the
--   "Electrified Water" alert closes the street and invalidates the route.
-- All people, phone numbers and e-mails are invented.

DO $$
DECLARE
  -- agencies
  a_gov uuid; a_police uuid; a_ems uuid; a_fire uuid;
  -- users
  u_admin uuid; u_gov_cmd uuid; u_analyst uuid; u_fire_cmd uuid;
  u_ff1 uuid; u_ff2 uuid; u_para1 uuid; u_para2 uuid; u_police uuid;
  -- teams / vehicles
  t_engine uuid; t_amb uuid; v_engine uuid; v_amb uuid;
  -- incident / ops
  inc uuid; z_staging uuid; m_rescue uuid; m_evac uuid;
  -- imagery / AI
  s_pre uuid; s_post uuid; r_pre uuid; r_post uuid; img_post uuid; img_frame1 uuid; img_frame2 uuid;
  job uuid; run_dmg uuid; run_det uuid; run_trk uuid; run_haz uuid;
  m_dmg uuid; m_det uuid; m_trk uuid; m_haz uuid;
  -- features
  trk uuid; case_id uuid; hosp uuid; route_id uuid; flood uuid; profile uuid;
  b uuid; a uuid;
  i int; j int;
  lon0 constant numeric := 31.2350;
  lat0 constant numeric := 30.0450;
  step constant numeric := 0.0020;      -- ≈ 190 m (lon) × 220 m (lat)
  node_ids bigint[] := '{}';
  nid bigint;
  seg bigint;
  grades damage_grade[] := ARRAY['NO_DAMAGE','MINOR','MAJOR','DESTROYED','MAJOR','NO_DAMAGE']::damage_grade[];
BEGIN
  ---------------------------------------------------------------- D1 identity
  INSERT INTO agencies (name, agency_type, phone) VALUES
    ('National Crisis Management Center', 'GOVERNMENT', '+20 2 0000 0001') RETURNING id INTO a_gov;
  INSERT INTO agencies (name, agency_type, parent_agency_id) VALUES
    ('Cairo Police Directorate', 'POLICE', NULL) RETURNING id INTO a_police;
  INSERT INTO agencies (name, agency_type) VALUES
    ('Cairo Ambulance Authority', 'EMS') RETURNING id INTO a_ems;
  INSERT INTO agencies (name, agency_type) VALUES
    ('Cairo Civil Defense', 'FIRE') RETURNING id INTO a_fire;

  -- password_hash values are placeholders; the API stores argon2 hashes.
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, status) VALUES
    (NULL, 'PLATFORM_ADMIN', 'Platform Admin', 'admin@resca.local', 'demo-not-a-real-hash', 'ACTIVE') RETURNING id INTO u_admin;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_gov, 'COMMANDER', 'Demo Crisis Coordinator', 'coordinator@gov.demo', 'demo-not-a-real-hash', 'Crisis Coordinator', 'ACTIVE') RETURNING id INTO u_gov_cmd;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_gov, 'ANALYST', 'Demo GIS Analyst', 'analyst@gov.demo', 'demo-not-a-real-hash', 'GIS Analyst', 'ACTIVE') RETURNING id INTO u_analyst;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_fire, 'COMMANDER', 'Demo Fire Chief', 'chief@fire.demo', 'demo-not-a-real-hash', 'Fire Chief', 'ACTIVE') RETURNING id INTO u_fire_cmd;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_fire, 'FIELD_RESPONDER', 'Demo Firefighter One', 'ff1@fire.demo', 'demo-not-a-real-hash', 'Firefighter', 'ACTIVE') RETURNING id INTO u_ff1;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_fire, 'FIELD_RESPONDER', 'Demo Firefighter Two', 'ff2@fire.demo', 'demo-not-a-real-hash', 'Firefighter', 'ACTIVE') RETURNING id INTO u_ff2;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_ems, 'FIELD_RESPONDER', 'Demo Paramedic One', 'para1@ems.demo', 'demo-not-a-real-hash', 'Paramedic', 'ACTIVE') RETURNING id INTO u_para1;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_ems, 'FIELD_RESPONDER', 'Demo Paramedic Two', 'para2@ems.demo', 'demo-not-a-real-hash', 'Paramedic', 'ACTIVE') RETURNING id INTO u_para2;
  INSERT INTO users (agency_id, role_code, full_name, email, password_hash, job_title, status) VALUES
    (a_police, 'FIELD_RESPONDER', 'Demo Police Officer', 'officer@police.demo', 'demo-not-a-real-hash', 'Police Officer', 'ACTIVE') RETURNING id INTO u_police;

  INSERT INTO teams (agency_id, name, team_type, home_base, status) VALUES
    (a_fire, 'Engine Crew A', 'FIRE_ENGINE', ST_SetSRID(ST_MakePoint(31.2330, 30.0440), 4326), 'DEPLOYED') RETURNING id INTO t_engine;
  INSERT INTO teams (agency_id, name, team_type, home_base, status) VALUES
    (a_ems, 'Ambulance Unit 14', 'AMBULANCE_UNIT', ST_SetSRID(ST_MakePoint(31.2330, 30.0460), 4326), 'DEPLOYED') RETURNING id INTO t_amb;
  INSERT INTO team_members (team_id, user_id, is_leader) VALUES
    (t_engine, u_ff1, true), (t_engine, u_ff2, false), (t_amb, u_para1, true), (t_amb, u_para2, false);
  INSERT INTO vehicles (agency_id, team_id, call_sign, vehicle_type, max_water_depth_cm) VALUES
    (a_fire, t_engine, 'ENG-A', 'FIRE_TRUCK', 50) RETURNING id INTO v_engine;
  INSERT INTO vehicles (agency_id, team_id, call_sign, vehicle_type, max_water_depth_cm) VALUES
    (a_ems, t_amb, 'AMB-14', 'AMBULANCE', 15) RETURNING id INTO v_amb;

  ---------------------------------------------------------------- D2 incident
  INSERT INTO incidents (code, name, disaster_type, severity, lead_agency_id, area, created_by)
  VALUES ('INC-2026-0001', 'Downtown Cairo Earthquake & Flash Flood (demo)', 'EARTHQUAKE', 4, a_gov,
          ST_Multi(ST_MakeEnvelope(31.2320, 30.0430, 31.2440, 30.0530, 4326)), u_gov_cmd)
  RETURNING id INTO inc;

  INSERT INTO incident_agencies (incident_id, agency_id, participation, status, invited_by, joined_at) VALUES
    (inc, a_gov,    'LEAD',    'ACTIVE', u_gov_cmd, now()),
    (inc, a_fire,   'SUPPORT', 'ACTIVE', u_gov_cmd, now()),
    (inc, a_ems,    'SUPPORT', 'ACTIVE', u_gov_cmd, now()),
    (inc, a_police, 'SUPPORT', 'ACTIVE', u_gov_cmd, now());

  INSERT INTO zones (incident_id, name, zone_type, geom, created_by) VALUES
    (inc, 'Staging Area West', 'STAGING_AREA',
     ST_Buffer(ST_SetSRID(ST_MakePoint(lon0, lat0 + step), 4326)::geography, 40)::geometry, u_gov_cmd)
  RETURNING id INTO z_staging;

  INSERT INTO missions (incident_id, agency_id, code, title, mission_type, priority, status, created_by)
  VALUES (inc, a_fire, 'M-001', 'Rescue trapped residents, Block C', 'SEARCH_RESCUE', 1, 'ASSIGNED', u_fire_cmd)
  RETURNING id INTO m_rescue;
  INSERT INTO missions (incident_id, agency_id, code, title, mission_type, priority, status, created_by)
  VALUES (inc, a_ems, 'M-002', 'Evacuate injured to hospital', 'MEDICAL_EVACUATION', 1, 'ASSIGNED', u_gov_cmd)
  RETURNING id INTO m_evac;

  INSERT INTO mission_assignments (mission_id, team_id, vehicle_id, assigned_by, response) VALUES
    (m_rescue, t_engine, v_engine, u_fire_cmd, 'ACCEPTED'),
    (m_evac,   t_amb,    v_amb,    u_gov_cmd,  'ACCEPTED');
  INSERT INTO mission_assignments (mission_id, user_id, assigned_by, response) VALUES
    (m_rescue, u_police, u_gov_cmd, 'ACCEPTED');   -- an individual added to a team mission

  ---------------------------------------------------------------- D3 imagery & AI
  SELECT id INTO m_dmg FROM ai_models WHERE task = 'DAMAGE_CLASSIFICATION' AND is_active;
  SELECT id INTO m_det FROM ai_models WHERE task = 'PERSON_DETECTION' AND is_active;
  SELECT id INTO m_trk FROM ai_models WHERE task = 'PERSON_TRACKING' AND is_active;
  SELECT id INTO m_haz FROM ai_models WHERE task = 'HAZARD_SEGMENTATION' AND is_active;

  INSERT INTO capture_sessions (incident_id, source_type, phase, provider, coverage, uploaded_by, status)
  VALUES (inc, 'SATELLITE', 'PRE_EVENT', 'Maxar Open Data (sample)',
          ST_MakeEnvelope(31.2320, 30.0430, 31.2440, 30.0530, 4326), u_analyst, 'READY') RETURNING id INTO s_pre;
  INSERT INTO capture_sessions (incident_id, mission_id, source_type, phase, provider, coverage, uploaded_by, status)
  VALUES (inc, m_rescue, 'DRONE', 'POST_EVENT', 'DJI Mavic 3T (sample)',
          ST_MakeEnvelope(31.2320, 30.0430, 31.2440, 30.0530, 4326), u_analyst, 'READY') RETURNING id INTO s_post;

  INSERT INTO raster_products (session_id, product_type, storage_key, resolution_m, bounds)
  VALUES (s_pre, 'ORTHOMOSAIC', 'demo/pre/ortho.tif', 0.5, ST_MakeEnvelope(31.2320, 30.0430, 31.2440, 30.0530, 4326))
  RETURNING id INTO r_pre;
  INSERT INTO raster_products (session_id, product_type, storage_key, resolution_m, bounds)
  VALUES (s_post, 'ORTHOMOSAIC', 'demo/post/ortho.tif', 0.03, ST_MakeEnvelope(31.2320, 30.0430, 31.2440, 30.0530, 4326))
  RETURNING id INTO r_post;

  INSERT INTO images (session_id, storage_key, sha256, width_px, height_px, captured_at,
                      camera_position, altitude_agl_m, gimbal_pitch, gsd_cm, gps_accuracy_m)
  VALUES (s_post, 'demo/post/DJI_0001.JPG', 'demo-sha-0001', 5280, 3956, now() - interval '2 hours',
          ST_SetSRID(ST_MakePoint(31.2390, 30.0480, 60), 4326), 60, -90, 1.6, 3.0)
  RETURNING id INTO img_post;
  INSERT INTO images (session_id, media_kind, frame_index, storage_key, sha256, width_px, height_px, captured_at, gsd_cm)
  VALUES (s_post, 'VIDEO_FRAME', 120, 'demo/post/video_frame_120.jpg', 'demo-sha-f120', 3840, 2160, now() - interval '90 minutes', 2.0)
  RETURNING id INTO img_frame1;
  INSERT INTO images (session_id, media_kind, frame_index, storage_key, sha256, width_px, height_px, captured_at, gsd_cm)
  VALUES (s_post, 'VIDEO_FRAME', 150, 'demo/post/video_frame_150.jpg', 'demo-sha-f150', 3840, 2160, now() - interval '89 minutes', 2.0)
  RETURNING id INTO img_frame2;

  INSERT INTO processing_jobs (incident_id, session_id, job_type, status, progress_pct, requested_by, started_at, finished_at)
  VALUES (inc, s_post, 'ANALYZE', 'SUCCEEDED', 100, u_analyst, now() - interval '80 minutes', now() - interval '70 minutes')
  RETURNING id INTO job;
  INSERT INTO inference_runs (job_id, model_id, pre_raster_id, post_raster_id, status, started_at, finished_at)
  VALUES (job, m_dmg, r_pre, r_post, 'SUCCEEDED', now() - interval '80 minutes', now() - interval '75 minutes') RETURNING id INTO run_dmg;
  INSERT INTO inference_runs (job_id, model_id, post_raster_id, params, status)
  VALUES (job, m_det, r_post, '{"conf_threshold":0.35}', 'SUCCEEDED') RETURNING id INTO run_det;
  INSERT INTO inference_runs (job_id, model_id, post_raster_id, status)
  VALUES (job, m_trk, r_post, 'SUCCEEDED') RETURNING id INTO run_trk;
  INSERT INTO inference_runs (job_id, model_id, post_raster_id, status)
  VALUES (job, m_haz, r_post, 'SUCCEEDED') RETURNING id INTO run_haz;

  ---------------------------------------------------------------- F2 road grid (4 × 4 nodes)
  FOR j IN 0..3 LOOP
    FOR i IN 0..3 LOOP
      INSERT INTO road_nodes (incident_id, geom)
      VALUES (inc, ST_SetSRID(ST_MakePoint(lon0 + i * step, lat0 + j * step), 4326))
      RETURNING id INTO nid;
      node_ids := node_ids || nid;              -- index = j*4 + i + 1
    END LOOP;
  END LOOP;

  FOR j IN 0..3 LOOP
    FOR i IN 0..3 LOOP
      IF i < 3 THEN   -- east-west street
        INSERT INTO road_segments (incident_id, source, target, geom, name, road_class, length_m, base_travel_s, condition, cost, reverse_cost)
        SELECT inc, node_ids[j*4+i+1], node_ids[j*4+i+2], g,
               CASE j WHEN 1 THEN 'El-Nile Street' WHEN 2 THEN 'Tahrir Street' ELSE 'Street ' || chr(65 + j) END,
               CASE WHEN j IN (1, 2) THEN 'PRIMARY'::road_class ELSE 'RESIDENTIAL'::road_class END,
               ST_Length(g::geography), ST_Length(g::geography) / 8.33, 'CLEAR',
               ST_Length(g::geography) / 8.33, ST_Length(g::geography) / 8.33
        FROM (SELECT ST_MakeLine((SELECT geom FROM road_nodes WHERE id = node_ids[j*4+i+1]),
                                 (SELECT geom FROM road_nodes WHERE id = node_ids[j*4+i+2])) AS g) x;
      END IF;
      IF j < 3 THEN   -- north-south street
        INSERT INTO road_segments (incident_id, source, target, geom, name, road_class, length_m, base_travel_s, condition, cost, reverse_cost)
        SELECT inc, node_ids[j*4+i+1], node_ids[(j+1)*4+i+1], g, 'Avenue ' || (i + 1), 'SECONDARY',
               ST_Length(g::geography), ST_Length(g::geography) / 8.33, 'CLEAR',
               ST_Length(g::geography) / 8.33, ST_Length(g::geography) / 8.33
        FROM (SELECT ST_MakeLine((SELECT geom FROM road_nodes WHERE id = node_ids[j*4+i+1]),
                                 (SELECT geom FROM road_nodes WHERE id = node_ids[(j+1)*4+i+1])) AS g) x;
      END IF;
    END LOOP;
  END LOOP;

  -- AI says a block on Avenue 2 is covered in debris.
  SELECT id INTO seg FROM road_segments WHERE incident_id = inc AND name = 'Avenue 2'
    ORDER BY id LIMIT 1;
  INSERT INTO road_condition_observations (segment_id, condition, confidence, inference_run_id)
  VALUES (seg, 'DEBRIS', 0.81, run_haz);
  UPDATE road_segments SET cost = cost * 4, reverse_cost = reverse_cost * 4 WHERE id = seg;

  ---------------------------------------------------------------- F1 buildings, damage, cost
  SELECT id INTO profile FROM cost_profiles ORDER BY valid_from DESC LIMIT 1;
  FOR i IN 1..6 LOOP
    INSERT INTO buildings (incident_id, external_ref, footprint, floors, occupancy, construction, source)
    VALUES (inc, 'osm-way-' || (1000 + i),
            ST_MakeEnvelope(lon0 + 0.0003 + (i - 1) * 0.0005, lat0 + step + 0.0003,
                            lon0 + 0.0006 + (i - 1) * 0.0005, lat0 + step + 0.0007, 4326),
            3 + (i % 3),
            CASE WHEN i = 4 THEN 'SCHOOL'::occupancy_type ELSE 'RESIDENTIAL'::occupancy_type END,
            'REINFORCED_CONCRETE', 'OSM')
    RETURNING id INTO b;

    INSERT INTO building_assessments (building_id, inference_run_id, method, damage_grade,
                                      p_no_damage, p_minor, p_major, p_destroyed, post_image_id)
    SELECT b, run_dmg, 'AI_BEFORE_AFTER', grades[i], p.n, p.mi, p.ma, p.d, img_post
    FROM (SELECT CASE grades[i] WHEN 'NO_DAMAGE' THEN 0.880 WHEN 'MINOR' THEN 0.150 WHEN 'MAJOR' THEN 0.050 ELSE 0.010 END AS n,
                 CASE grades[i] WHEN 'NO_DAMAGE' THEN 0.090 WHEN 'MINOR' THEN 0.700 WHEN 'MAJOR' THEN 0.150 ELSE 0.040 END AS mi,
                 CASE grades[i] WHEN 'NO_DAMAGE' THEN 0.020 WHEN 'MINOR' THEN 0.120 WHEN 'MAJOR' THEN 0.700 ELSE 0.150 END AS ma,
                 CASE grades[i] WHEN 'NO_DAMAGE' THEN 0.010 WHEN 'MINOR' THEN 0.030 WHEN 'MAJOR' THEN 0.100 ELSE 0.800 END AS d) p
    RETURNING id INTO a;

    -- cost = floor area × unit rate × repair ratio (low/high)
    INSERT INTO cost_estimates (building_id, assessment_id, cost_profile_id, floor_area_m2,
                                repair_ratio_low, repair_ratio_high, cost_low, cost_high, currency, assumptions)
    SELECT bl.id, a, profile, bl.area_m2 * bl.floors, rr.ratio_low, rr.ratio_high,
           round(bl.area_m2 * bl.floors * ur.cost_per_m2_low  * rr.ratio_low, 2),
           round(bl.area_m2 * bl.floors * ur.cost_per_m2_high * rr.ratio_high, 2),
           cp.currency, jsonb_build_object('floors', 'from OSM building:levels', 'construction', 'assumed reinforced concrete')
    FROM buildings bl
    JOIN cost_profiles cp ON cp.id = profile
    JOIN cost_profile_unit_rates ur ON ur.profile_id = profile AND ur.occupancy = bl.occupancy AND ur.construction = bl.construction
    JOIN cost_profile_repair_ratios rr ON rr.profile_id = profile AND rr.damage_grade = grades[i]
    WHERE bl.id = b;
  END LOOP;

  -- An analyst confirms the "destroyed" verdict.
  UPDATE building_assessments SET review_status = 'CONFIRMED', reviewed_by = u_analyst, reviewed_at = now()
   WHERE damage_grade = 'DESTROYED';

  ---------------------------------------------------------------- F3/F4 persons
  INSERT INTO person_tracks (incident_id, inference_run_id, tracker_local_id, first_seen_at, last_seen_at,
                             last_position, last_position_error_m, movement_state, max_confidence, detection_count)
  VALUES (inc, run_trk, 7, now() - interval '90 minutes', now() - interval '89 minutes',
          ST_SetSRID(ST_MakePoint(lon0 + 3 * step, lat0 + step + 0.0002), 4326), 3.5, 'STATIONARY', 0.74, 2)
  RETURNING id INTO trk;

  INSERT INTO person_detections (incident_id, inference_run_id, image_id, track_id, bbox_x, bbox_y, bbox_w, bbox_h,
                                 confidence, visibility, occlusion_ratio, posture, location, location_error_m, detected_at)
  VALUES
    (inc, run_det, img_frame1, trk, 1840, 960, 42, 30, 0.61, 'PARTIAL', 0.55, 'LYING',
     ST_SetSRID(ST_MakePoint(lon0 + 3 * step, lat0 + step + 0.0002), 4326), 3.8, now() - interval '90 minutes'),
    (inc, run_det, img_frame2, trk, 1843, 958, 40, 31, 0.74, 'HEAD_ONLY', 0.70, 'LYING',
     ST_SetSRID(ST_MakePoint(lon0 + 3 * step, lat0 + step + 0.0002), 4326), 3.5, now() - interval '89 minutes');

  INSERT INTO facilities (agency_id, name, facility_type, geom, capacity_total, capacity_available)
  VALUES (a_ems, 'Demo General Hospital', 'HOSPITAL',
          ST_SetSRID(ST_MakePoint(lon0 + 3 * step + 0.0010, lat0 + 3 * step), 4326), 300, 42)
  RETURNING id INTO hosp;

  INSERT INTO assistance_cases (incident_id, code, source, track_id, location, location_error_m,
                                people_count, triage, status, priority_score, assigned_mission_id,
                                verified_by, verified_at)
  VALUES (inc, 'CASE-0001', 'AI_DETECTION', trk,
          ST_SetSRID(ST_MakePoint(lon0 + 3 * step, lat0 + step + 0.0002), 4326), 3.5,
          1, 'IMMEDIATE', 'ASSIGNED', 92.5, m_rescue, u_fire_cmd, now())
  RETURNING id INTO case_id;

  ---------------------------------------------------------------- live positions
  INSERT INTO responder_positions (user_id, incident_id, mission_id, recorded_at, geom, accuracy_m, speed_mps, battery_pct) VALUES
    (u_ff1,  inc, m_rescue, now() - interval '2 minutes', ST_SetSRID(ST_MakePoint(lon0 + 0.0002, lat0 + step), 4326), 4.0, 0.0, 81),
    (u_ff1,  inc, m_rescue, now() - interval '1 minute',  ST_SetSRID(ST_MakePoint(lon0 + 0.0004, lat0 + step), 4326), 4.0, 1.2, 80),
    (u_para1, inc, m_evac,  now() - interval '1 minute',  ST_SetSRID(ST_MakePoint(lon0 + 2 * step + 0.0004, lat0 + step + 0.0001), 4326), 5.0, 0.0, 64);

  ---------------------------------------------------------------- F2 planned route (before the alert)
  -- Engine Crew A: staging (west end of El-Nile Street) → the trapped person (east end).
  INSERT INTO routes (incident_id, mission_id, requested_by, vehicle_type, origin, destination,
                      destination_case_id, algorithm, rank, geom, length_m, est_travel_s, risk_score)
  SELECT inc, m_rescue, u_fire_cmd, 'FIRE_TRUCK',
         (SELECT geom FROM road_nodes WHERE id = node_ids[5]),
         (SELECT geom FROM road_nodes WHERE id = node_ids[8]),
         case_id, 'ASTAR', 1,
         ST_LineMerge(ST_Union(s.geom)), sum(s.length_m), sum(s.base_travel_s), 0.20
  FROM road_segments s
  WHERE s.incident_id = inc AND s.name = 'El-Nile Street'
  RETURNING id INTO route_id;

  INSERT INTO route_segments (route_id, seq, segment_id)
  SELECT route_id, row_number() OVER (ORDER BY ST_XMin(s.geom)), s.id
  FROM road_segments s WHERE s.incident_id = inc AND s.name = 'El-Nile Street';

  ---------------------------------------------------------------- F5 hazards
  -- A live 11 kV line runs along El-Nile Street …
  INSERT INTO infrastructure_assets (incident_id, asset_type, geom, voltage_kv, operator, power_state, state_updated_at)
  VALUES (inc, 'POWER_LINE',
          ST_SetSRID(ST_MakeLine(ST_MakePoint(lon0 + 0.0010, lat0 + step + 0.00005),
                                 ST_MakePoint(lon0 + 2 * step + 0.0010, lat0 + step + 0.00005)), 4326),
          11, 'Demo Electricity Distribution Co.', 'ENERGIZED', now());
  -- … and a gas pipeline sits far away (no interaction).
  INSERT INTO infrastructure_assets (incident_id, asset_type, geom, operator)
  VALUES (inc, 'GAS_PIPELINE',
          ST_SetSRID(ST_MakeLine(ST_MakePoint(lon0, lat0 + 3 * step), ST_MakePoint(lon0 + 3 * step, lat0 + 3 * step)), 4326),
          'Demo Gas Co.');

  -- AI sees floodwater 20 m south of the line.
  INSERT INTO hazards (incident_id, hazard_type, geom, severity, confidence, origin, inference_run_id, status, attributes)
  VALUES (inc, 'FLOOD_WATER',
          ST_Buffer(ST_SetSRID(ST_MakePoint(lon0 + 2 * step - 0.0004, lat0 + step - 0.0002), 4326)::geography, 30)::geometry,
          3, 0.88, 'AI_DETECTED', run_haz, 'CONFIRMED', '{"water_depth_cm": 35}')
  RETURNING id INTO flood;

  -- A firefighter reports a building that may collapse next to Avenue 4.
  INSERT INTO hazards (incident_id, hazard_type, geom, severity, origin, reported_by, status)
  VALUES (inc, 'COLLAPSE_RISK', ST_SetSRID(ST_MakePoint(lon0 + 3 * step + 0.0001, lat0 + 2 * step + 0.0010), 4326),
          4, 'RESPONDER_REPORTED', u_ff2, 'CONFIRMED');

  ---------------------------------------------------------------- citizen channel
  INSERT INTO citizens (phone, preferred_language, phone_verified_at) VALUES ('+20 100 000 0000', 'ar', now());
  INSERT INTO citizen_requests (citizen_id, request_type, location, people_count, description)
  SELECT id, 'TRAPPED', ST_SetSRID(ST_MakePoint(lon0 + step + 0.0005, lat0 + 2 * step + 0.0003), 4326), 3,
         'Family of three on the roof, stairs collapsed'
  FROM citizens WHERE phone = '+20 100 000 0000';

  ---------------------------------------------------------------- F6 report draft
  INSERT INTO reports (incident_id, report_type, title, status, stats_snapshot, generated_by)
  SELECT inc, 'SITUATION_REPORT', 'SITREP #1 — Downtown Cairo', 'DRAFT', to_jsonb(s), u_analyst
  FROM v_incident_damage_summary s WHERE s.incident_id = inc;

  RAISE NOTICE 'Demo incident % created', inc;
END $$;

-- Fire the compound hazard rules (Electrified Water + Falling-Debris Zone).
SELECT evaluate_hazard_rules(id) AS new_alert_id FROM incidents WHERE code = 'INC-2026-0001';
