-- D2 · Incidents & Operations (6 tables)
-- One shared Incident per disaster (Incident Command System style). The lead
-- agency invites the others; each agency runs its own Missions.

CREATE TABLE incidents (
  id             uuid            PRIMARY KEY DEFAULT uuidv7(),
  code           text            NOT NULL UNIQUE,              -- "INC-2026-0007"
  name           text            NOT NULL,
  disaster_type  disaster_type   NOT NULL,
  status         incident_status NOT NULL DEFAULT 'ACTIVE',
  severity       smallint        NOT NULL CHECK (severity BETWEEN 1 AND 5),
  lead_agency_id uuid            NOT NULL REFERENCES agencies(id),
  area           geometry(MultiPolygon, 4326) NOT NULL,         -- the AOI everything lives inside
  is_historical  boolean         NOT NULL DEFAULT false,        -- reference events for similar-case search
  started_at     timestamptz     NOT NULL DEFAULT now(),
  closed_at      timestamptz,
  created_by     uuid            REFERENCES users(id),
  created_at     timestamptz     NOT NULL DEFAULT now(),
  updated_at     timestamptz     NOT NULL DEFAULT now(),
  CONSTRAINT incidents_closed_after_start CHECK (closed_at IS NULL OR closed_at >= started_at),
  CONSTRAINT incidents_closed_has_time    CHECK ((status = 'CLOSED') = (closed_at IS NOT NULL))
);
CREATE INDEX incidents_area_gix   ON incidents USING gist (area);
CREATE INDEX incidents_status_idx ON incidents (status) WHERE status <> 'CLOSED';
CREATE TRIGGER incidents_updated_at BEFORE UPDATE ON incidents FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE incident_agencies (
  incident_id   uuid                 NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  agency_id     uuid                 NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  participation participation_role   NOT NULL DEFAULT 'SUPPORT',
  status        participation_status NOT NULL DEFAULT 'INVITED',
  invited_by    uuid                 REFERENCES users(id),
  invited_at    timestamptz          NOT NULL DEFAULT now(),
  joined_at     timestamptz,
  PRIMARY KEY (incident_id, agency_id)
);
-- Exactly one lead agency per incident.
CREATE UNIQUE INDEX incident_agencies_one_lead_uq ON incident_agencies (incident_id) WHERE participation = 'LEAD';
-- "Which incidents can my agency see?"
CREATE INDEX incident_agencies_agency_active_idx ON incident_agencies (agency_id) WHERE status = 'ACTIVE';

CREATE TABLE zones (
  id          uuid      PRIMARY KEY DEFAULT uuidv7(),
  incident_id uuid      NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  name        text      NOT NULL,
  zone_type   zone_type NOT NULL,
  geom        geometry(Geometry, 4326) NOT NULL,
  created_by  uuid      REFERENCES users(id),
  created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX zones_incident_idx ON zones (incident_id, zone_type);
CREATE INDEX zones_geom_gix     ON zones USING gist (geom);

CREATE TABLE missions (
  id             uuid           PRIMARY KEY DEFAULT uuidv7(),
  incident_id    uuid           NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  agency_id      uuid           NOT NULL REFERENCES agencies(id),   -- owning agency
  code           text           NOT NULL,
  title          text           NOT NULL,
  mission_type   mission_type   NOT NULL,
  priority       smallint       NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 4),
  status         mission_status NOT NULL DEFAULT 'PLANNED',
  target_zone_id uuid           REFERENCES zones(id) ON DELETE SET NULL,
  target_geom    geometry(Geometry, 4326),
  created_by     uuid           REFERENCES users(id),
  created_at     timestamptz    NOT NULL DEFAULT now(),
  updated_at     timestamptz    NOT NULL DEFAULT now(),
  started_at     timestamptz,
  completed_at   timestamptz,
  CONSTRAINT missions_incident_code_uq UNIQUE (incident_id, code),
  CONSTRAINT missions_completed_after_start CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);
CREATE INDEX missions_incident_status_idx ON missions (incident_id, status);
CREATE INDEX missions_agency_idx          ON missions (agency_id);
CREATE INDEX missions_target_geom_gix     ON missions USING gist (target_geom);
CREATE TRIGGER missions_updated_at BEFORE UPDATE ON missions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE mission_assignments (
  id          uuid                PRIMARY KEY DEFAULT uuidv7(),
  mission_id  uuid                NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
  team_id     uuid                REFERENCES teams(id),
  user_id     uuid                REFERENCES users(id),
  vehicle_id  uuid                REFERENCES vehicles(id),
  assigned_by uuid                REFERENCES users(id),
  assigned_at timestamptz         NOT NULL DEFAULT now(),
  released_at timestamptz,
  response    assignment_response NOT NULL DEFAULT 'PENDING',
  -- A mission is assigned to a whole team OR to one responder.
  CONSTRAINT mission_assignments_team_xor_user CHECK (num_nonnulls(team_id, user_id) = 1)
);
CREATE INDEX mission_assignments_mission_idx ON mission_assignments (mission_id) WHERE released_at IS NULL;
CREATE INDEX mission_assignments_team_idx    ON mission_assignments (team_id)    WHERE released_at IS NULL;
CREATE INDEX mission_assignments_user_idx    ON mission_assignments (user_id)    WHERE released_at IS NULL;

CREATE TABLE mission_status_history (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  mission_id  uuid           NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
  from_status mission_status,
  to_status   mission_status NOT NULL,
  changed_by  uuid           REFERENCES users(id),
  changed_at  timestamptz    NOT NULL DEFAULT now(),
  note        text
);
CREATE INDEX mission_status_history_mission_idx ON mission_status_history (mission_id, changed_at);

-- Record every mission status change automatically.
CREATE OR REPLACE FUNCTION log_mission_status() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' OR NEW.status IS DISTINCT FROM OLD.status THEN
    INSERT INTO mission_status_history (mission_id, from_status, to_status)
    VALUES (NEW.id, CASE WHEN TG_OP = 'UPDATE' THEN OLD.status END, NEW.status);
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER missions_status_history AFTER INSERT OR UPDATE OF status ON missions
  FOR EACH ROW EXECUTE FUNCTION log_mission_status();
