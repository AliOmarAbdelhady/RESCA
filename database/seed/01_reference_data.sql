-- Reference data required in every environment: roles, permissions, hazard
-- rules, a cost profile and the model registry.

-- Roles -----------------------------------------------------------------------
INSERT INTO roles (code, name, scope) VALUES
  ('PLATFORM_ADMIN',  'Platform Admin',     'PLATFORM'),
  ('AGENCY_ADMIN',    'Agency Admin',       'AGENCY'),
  ('COMMANDER',       'Commander',          'AGENCY'),
  ('ANALYST',         'Analyst / Operator', 'AGENCY'),
  ('FIELD_RESPONDER', 'Field Responder',    'AGENCY');

-- Permissions -----------------------------------------------------------------
INSERT INTO permissions (code, description) VALUES
  ('agency.manage',        'Create and edit agencies'),
  ('model.manage',         'Register and activate AI models'),
  ('rule.manage',          'Create and edit compound hazard rules'),
  ('user.manage',          'Invite, edit and suspend users of the agency'),
  ('team.manage',          'Manage teams and vehicles of the agency'),
  ('incident.create',      'Declare a new incident'),
  ('incident.invite',      'Invite other agencies to an incident'),
  ('incident.view',        'View incidents the agency has joined'),
  ('mission.create',       'Create missions'),
  ('mission.assign',       'Assign missions to teams or responders'),
  ('mission.update_status','Update the status of an assigned mission'),
  ('imagery.upload',       'Upload drone or satellite imagery'),
  ('analysis.run',         'Run AI analysis jobs'),
  ('assessment.review',    'Confirm or correct AI damage assessments'),
  ('cost.edit_profile',    'Edit cost profiles and unit rates'),
  ('route.plan',           'Plan rescue routes'),
  ('case.verify',          'Verify AI detections and citizen requests'),
  ('case.triage',          'Set START triage on assistance cases'),
  ('case.update',          'Update case status in the field'),
  ('hazard.report',        'Report a hazard from the field'),
  ('alert.resolve',        'Acknowledge and resolve compound alerts'),
  ('sos.raise',            'Raise an SOS'),
  ('sos.respond',          'Acknowledge and resolve SOS alerts'),
  ('position.share',       'Share live GPS position'),
  ('report.generate',      'Generate reports'),
  ('report.approve',       'Approve and publish reports'),
  ('report.share',         'Share reports with other agencies');

INSERT INTO role_permissions (role_code, permission_code)
SELECT 'PLATFORM_ADMIN', code FROM permissions;

INSERT INTO role_permissions (role_code, permission_code)
SELECT 'AGENCY_ADMIN', unnest(ARRAY['user.manage','team.manage','incident.view','report.generate']);

INSERT INTO role_permissions (role_code, permission_code)
SELECT 'COMMANDER', unnest(ARRAY[
  'incident.create','incident.invite','incident.view','mission.create','mission.assign',
  'mission.update_status','assessment.review','route.plan','case.verify','case.triage',
  'alert.resolve','sos.respond','report.generate','report.approve','report.share']);

INSERT INTO role_permissions (role_code, permission_code)
SELECT 'ANALYST', unnest(ARRAY[
  'incident.view','imagery.upload','analysis.run','assessment.review','cost.edit_profile',
  'route.plan','case.verify','case.triage','hazard.report','report.generate']);

INSERT INTO role_permissions (role_code, permission_code)
SELECT 'FIELD_RESPONDER', unnest(ARRAY[
  'incident.view','mission.update_status','case.update','case.triage','hazard.report',
  'sos.raise','position.share']);

-- Compound hazard rules (F5) ---------------------------------------------------
INSERT INTO hazard_rules (code, name, description, primary_hazard_type, secondary_kind,
                          secondary_types, max_distance_m, danger_buffer_m, resulting_severity,
                          closes_roads, warning_template) VALUES
  ('ELECTRIFIED_WATER', 'Electrified Water',
   'Floodwater within 30 m of an energized power line or transformer.',
   'FLOOD_WATER', 'ASSET', ARRAY['POWER_LINE','TRANSFORMER','SUBSTATION'], 30, 25, 5, true,
   'Electrified water near {street}. Do NOT enter the water. Wait for power to be cut.'),
  ('ELECTRIFIED_WATER_DOWNED_LINE', 'Electrified Water (downed line)',
   'Floodwater touching or near a fallen power line.',
   'FLOOD_WATER', 'HAZARD', ARRAY['DOWNED_POWER_LINE'], 30, 30, 5, true,
   'Fallen power line in floodwater near {street}. Do NOT enter.'),
  ('FIRE_GAS_EXPLOSION', 'Explosion Risk',
   'Fire within 50 m of a gas leak.',
   'FIRE', 'HAZARD', ARRAY['GAS_LEAK'], 50, 100, 5, true,
   'Explosion risk near {street}: fire next to a gas leak. Keep 100 m away.'),
  ('FIRE_NEAR_FUEL', 'Explosion Risk (fuel / gas asset)',
   'Fire within 50 m of a gas pipeline or fuel station.',
   'FIRE', 'ASSET', ARRAY['GAS_PIPELINE','FUEL_STATION'], 50, 100, 5, true,
   'Fire near fuel or gas infrastructure on {street}. Keep 100 m away.'),
  ('COLLAPSE_ON_ROAD', 'Falling-Debris Zone',
   'A building at risk of collapse within 15 m of a road.',
   'COLLAPSE_RISK', 'ROAD', ARRAY['ANY'], 15, 20, 4, true,
   'Building may collapse onto {street}. Use another route.');

-- Cost profile (F1) -----------------------------------------------------------
-- Repair ratios follow FEMA HAZUS damage-state ranges; unit rates are
-- illustrative placeholders for the team to replace with sourced local rates.
WITH p AS (
  INSERT INTO cost_profiles (name, region, currency, source, valid_from)
  VALUES ('Egypt 2026 urban (illustrative)', 'Greater Cairo', 'EGP',
          'FEMA HAZUS repair ratios; placeholder local unit rates', DATE '2026-01-01')
  RETURNING id
), ratios AS (
  INSERT INTO cost_profile_repair_ratios (profile_id, damage_grade, ratio_low, ratio_high)
  SELECT p.id, v.g::damage_grade, v.lo, v.hi FROM p,
  (VALUES ('NO_DAMAGE', 0.000, 0.020), ('MINOR', 0.020, 0.100),
          ('MAJOR', 0.100, 0.500), ('DESTROYED', 0.800, 1.000)) AS v(g, lo, hi)
)
INSERT INTO cost_profile_unit_rates (profile_id, occupancy, construction, cost_per_m2_low, cost_per_m2_high)
SELECT p.id, o::occupancy_type, c::construction_type,
       base * mult, base * mult * 1.35
FROM p,
  (VALUES ('RESIDENTIAL', 1.00), ('COMMERCIAL', 1.20), ('HOSPITAL', 2.20), ('SCHOOL', 1.30),
          ('GOVERNMENT', 1.40), ('INDUSTRIAL', 0.90), ('RELIGIOUS', 1.30), ('UNKNOWN', 1.00)) AS occ(o, mult),
  (VALUES ('REINFORCED_CONCRETE', 12000), ('MASONRY', 9000), ('STEEL', 14000),
          ('WOOD', 7000), ('UNKNOWN', 11000)) AS con(c, base);

-- AI model registry ---------------------------------------------------------------
INSERT INTO ai_models (name, version, task, architecture, training_datasets, is_active) VALUES
  ('building-seg',        '1.0.0', 'BUILDING_SEGMENTATION', 'U-Net ResNet34',         ARRAY['xBD'], true),
  ('damage-classifier',   '1.0.0', 'DAMAGE_CLASSIFICATION', 'DINOv2 + MLP',           ARRAY['xBD','RescueNet'], true),
  ('change-detector',     '1.0.0', 'CHANGE_DETECTION',      'Siamese U-Net',          ARRAY['xBD'], true),
  ('person-detector',     '1.0.0', 'PERSON_DETECTION',      'YOLOv8s',                ARRAY['SARD','VisDrone','POP'], true),
  ('person-tracker',      '1.0.0', 'PERSON_TRACKING',       'ByteTrack',              ARRAY[]::text[], true),
  ('road-condition',      '1.0.0', 'ROAD_CONDITION',        'SegFormer-B2',           ARRAY['RescueNet','FloodNet'], true),
  ('hazard-segmentation', '1.0.0', 'HAZARD_SEGMENTATION',   'SegFormer-B2',           ARRAY['FloodNet','RescueNet'], true),
  ('fire-smoke',          '1.0.0', 'FIRE_SMOKE_DETECTION',  'YOLOv8s',                ARRAY['D-Fire','FLAME 2'], true),
  ('scene-embedder',      '1.0.0', 'IMAGE_EMBEDDING',       'DINOv2 ViT-B/14 (768-d)', ARRAY['xBD'], true);
