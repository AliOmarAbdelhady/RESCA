-- D4c · F3/F4 Person detection, tracking & assistance cases (5 tables)
-- Three levels: raw AI detection → track (same person across frames) →
-- assistance case (a person a human decided needs help).
-- Scope: visible or partially visible persons only, never "under rubble".

CREATE TABLE person_tracks (
  id                    uuid           PRIMARY KEY DEFAULT uuidv7(),
  incident_id           uuid           NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  inference_run_id      uuid           NOT NULL REFERENCES inference_runs(id) ON DELETE CASCADE,
  tracker_local_id      integer        NOT NULL,          -- ByteTrack id within that run
  first_seen_at         timestamptz    NOT NULL,
  last_seen_at          timestamptz    NOT NULL,
  last_position         geometry(Point, 4326) NOT NULL,
  last_position_error_m numeric(7,2)   CHECK (last_position_error_m >= 0),
  movement_state        movement_state NOT NULL DEFAULT 'UNKNOWN',  -- long STATIONARY → possible injury
  max_confidence        numeric(4,3)   CHECK (max_confidence BETWEEN 0 AND 1),
  detection_count       integer        NOT NULL DEFAULT 0 CHECK (detection_count >= 0),
  CONSTRAINT person_tracks_run_local_uq UNIQUE (inference_run_id, tracker_local_id),
  CONSTRAINT person_tracks_time_order   CHECK (last_seen_at >= first_seen_at)
);
CREATE INDEX person_tracks_incident_idx  ON person_tracks (incident_id, last_seen_at DESC);
CREATE INDEX person_tracks_position_gix  ON person_tracks USING gist (last_position);

CREATE TABLE person_detections (
  id               bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  incident_id      uuid             NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  inference_run_id uuid             NOT NULL REFERENCES inference_runs(id) ON DELETE CASCADE,
  image_id         uuid             NOT NULL REFERENCES images(id) ON DELETE CASCADE,
  track_id         uuid             REFERENCES person_tracks(id) ON DELETE SET NULL,
  bbox_x           integer          NOT NULL CHECK (bbox_x >= 0),
  bbox_y           integer          NOT NULL CHECK (bbox_y >= 0),
  bbox_w           integer          NOT NULL CHECK (bbox_w > 0),
  bbox_h           integer          NOT NULL CHECK (bbox_h > 0),
  confidence       numeric(4,3)     NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  visibility       visibility_level NOT NULL,              -- the "partial body only" requirement
  occlusion_ratio  numeric(3,2)     CHECK (occlusion_ratio BETWEEN 0 AND 1),
  posture          posture          NOT NULL DEFAULT 'UNKNOWN',
  location         geometry(Point, 4326) NOT NULL,
  location_error_m numeric(7,2)     NOT NULL CHECK (location_error_m >= 0),  -- uncertainty radius
  detected_at      timestamptz      NOT NULL
);
-- High volume, append-only: BRIN on time is tiny and fast.
CREATE INDEX person_detections_detected_brin ON person_detections USING brin (detected_at);
CREATE INDEX person_detections_location_gix  ON person_detections USING gist (location);
CREATE INDEX person_detections_track_idx     ON person_detections (track_id);
CREATE INDEX person_detections_image_idx     ON person_detections (image_id);
CREATE INDEX person_detections_run_idx       ON person_detections (inference_run_id);

CREATE TABLE facilities (
  id                 uuid          PRIMARY KEY DEFAULT uuidv7(),
  agency_id          uuid          REFERENCES agencies(id) ON DELETE SET NULL,
  name               text          NOT NULL,
  facility_type      facility_type NOT NULL,
  geom               geometry(Point, 4326) NOT NULL,
  capacity_total     integer       CHECK (capacity_total >= 0),
  capacity_available integer       CHECK (capacity_available >= 0),
  updated_at         timestamptz   NOT NULL DEFAULT now(),
  CONSTRAINT facilities_capacity CHECK (capacity_available IS NULL OR capacity_total IS NULL OR capacity_available <= capacity_total)
);
CREATE INDEX facilities_geom_gix ON facilities USING gist (geom);
CREATE INDEX facilities_type_idx ON facilities (facility_type);
CREATE TRIGGER facilities_updated_at BEFORE UPDATE ON facilities FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE assistance_cases (
  id                         uuid            PRIMARY KEY DEFAULT uuidv7(),
  incident_id                uuid            NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  code                       text            NOT NULL,                 -- "CASE-0142"
  source                     case_source     NOT NULL,
  track_id                   uuid            REFERENCES person_tracks(id) ON DELETE SET NULL,
  citizen_request_id         uuid            REFERENCES citizen_requests(id) ON DELETE SET NULL,
  reported_by                uuid            REFERENCES users(id),
  location                   geometry(Point, 4326) NOT NULL,
  location_error_m           numeric(7,2)    CHECK (location_error_m >= 0),
  building_id                uuid            REFERENCES buildings(id) ON DELETE SET NULL,  -- trapped inside
  people_count               smallint        NOT NULL DEFAULT 1 CHECK (people_count > 0),
  triage                     triage_category NOT NULL DEFAULT 'UNTRIAGED',
  status                     case_status     NOT NULL DEFAULT 'DETECTED',
  priority_score             numeric(6,2)    NOT NULL DEFAULT 0,
  assigned_mission_id        uuid            REFERENCES missions(id) ON DELETE SET NULL,
  transported_to_facility_id uuid            REFERENCES facilities(id) ON DELETE SET NULL,
  verified_by                uuid            REFERENCES users(id),
  verified_at                timestamptz,
  created_at                 timestamptz     NOT NULL DEFAULT now(),
  updated_at                 timestamptz     NOT NULL DEFAULT now(),
  closed_at                  timestamptz,
  CONSTRAINT assistance_cases_incident_code_uq UNIQUE (incident_id, code),
  -- The source column must match the link that proves it.
  CONSTRAINT assistance_cases_source_link CHECK (
       (source = 'AI_DETECTION'     AND track_id IS NOT NULL)
    OR (source = 'CITIZEN_REQUEST'  AND citizen_request_id IS NOT NULL)
    OR (source = 'RESPONDER_REPORT' AND reported_by IS NOT NULL)),
  CONSTRAINT assistance_cases_transport_has_facility CHECK (status <> 'TRANSPORTED' OR transported_to_facility_id IS NOT NULL),
  CONSTRAINT assistance_cases_closed_states CHECK (
    (status IN ('RESCUED', 'TRANSPORTED', 'DECEASED', 'FALSE_ALARM')) = (closed_at IS NOT NULL))
);
CREATE INDEX assistance_cases_open_idx     ON assistance_cases (incident_id, priority_score DESC) WHERE closed_at IS NULL;
CREATE INDEX assistance_cases_location_gix ON assistance_cases USING gist (location);
CREATE INDEX assistance_cases_mission_idx  ON assistance_cases (assigned_mission_id);
CREATE INDEX assistance_cases_track_idx    ON assistance_cases (track_id);
CREATE INDEX assistance_cases_request_idx  ON assistance_cases (citizen_request_id);
CREATE TRIGGER assistance_cases_updated_at BEFORE UPDATE ON assistance_cases FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE case_events (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id     uuid            NOT NULL REFERENCES assistance_cases(id) ON DELETE CASCADE,
  event_type  case_event_type NOT NULL,
  from_status case_status,
  to_status   case_status,
  triage      triage_category,
  note        text,
  media_id    uuid            REFERENCES media_files(id) ON DELETE SET NULL,
  actor_id    uuid            REFERENCES users(id),
  created_at  timestamptz     NOT NULL DEFAULT now(),
  CONSTRAINT case_events_status_payload CHECK (event_type <> 'STATUS' OR to_status IS NOT NULL),
  CONSTRAINT case_events_triage_payload CHECK (event_type <> 'TRIAGE' OR triage IS NOT NULL),
  CONSTRAINT case_events_photo_payload  CHECK (event_type <> 'PHOTO'  OR media_id IS NOT NULL)
);
CREATE INDEX case_events_case_idx ON case_events (case_id, created_at);

-- Log status and triage changes automatically.
CREATE OR REPLACE FUNCTION log_case_changes() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO case_events (case_id, event_type, to_status) VALUES (NEW.id, 'STATUS', NEW.status);
  ELSE
    IF NEW.status IS DISTINCT FROM OLD.status THEN
      INSERT INTO case_events (case_id, event_type, from_status, to_status)
      VALUES (NEW.id, 'STATUS', OLD.status, NEW.status);
    END IF;
    IF NEW.triage IS DISTINCT FROM OLD.triage THEN
      INSERT INTO case_events (case_id, event_type, triage) VALUES (NEW.id, 'TRIAGE', NEW.triage);
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER assistance_cases_log AFTER INSERT OR UPDATE OF status, triage ON assistance_cases
  FOR EACH ROW EXECUTE FUNCTION log_case_changes();
