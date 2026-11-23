-- D4b (part 2) · F2 Routes + F5 road closures (3 tables)
-- Created after cases, facilities and alerts because routes point at all three.

CREATE TABLE routes (
  id                      uuid            PRIMARY KEY DEFAULT uuidv7(),
  incident_id             uuid            NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  mission_id              uuid            REFERENCES missions(id) ON DELETE SET NULL,
  requested_by            uuid            REFERENCES users(id),
  vehicle_type            vehicle_type    NOT NULL,
  origin                  geometry(Point, 4326) NOT NULL,
  destination             geometry(Point, 4326) NOT NULL,
  destination_case_id     uuid            REFERENCES assistance_cases(id) ON DELETE SET NULL,
  destination_facility_id uuid            REFERENCES facilities(id) ON DELETE SET NULL,
  algorithm               route_algorithm NOT NULL DEFAULT 'ASTAR',
  rank                    smallint        NOT NULL DEFAULT 1 CHECK (rank >= 1),   -- 1 = primary
  geom                    geometry(LineString, 4326) NOT NULL,
  length_m                numeric(10,2)   NOT NULL CHECK (length_m >= 0),
  est_travel_s            numeric(10,2)   NOT NULL CHECK (est_travel_s >= 0),
  risk_score              numeric(6,3)    NOT NULL DEFAULT 0,
  status                  route_status    NOT NULL DEFAULT 'ACTIVE',
  invalidated_by_alert_id uuid            REFERENCES compound_alerts(id) ON DELETE SET NULL,
  computed_at             timestamptz     NOT NULL DEFAULT now(),
  CONSTRAINT routes_one_destination_target CHECK (num_nonnulls(destination_case_id, destination_facility_id) <= 1),
  CONSTRAINT routes_invalidation_reason CHECK (invalidated_by_alert_id IS NULL OR status = 'INVALIDATED')
);
CREATE INDEX routes_active_idx  ON routes (incident_id) WHERE status = 'ACTIVE';
CREATE INDEX routes_mission_idx ON routes (mission_id);
CREATE INDEX routes_geom_gix    ON routes USING gist (geom);
CREATE INDEX routes_origin_gix  ON routes USING gist (origin);
CREATE INDEX routes_dest_gix    ON routes USING gist (destination);

CREATE TABLE route_segments (
  route_id   uuid    NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
  seq        integer NOT NULL CHECK (seq >= 1),
  segment_id bigint  NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
  PRIMARY KEY (route_id, seq)
);
-- "Which routes use this (now closed) road?" — one indexed lookup.
CREATE INDEX route_segments_segment_idx ON route_segments (segment_id);

CREATE TABLE alert_closed_segments (
  alert_id         uuid           NOT NULL REFERENCES compound_alerts(id) ON DELETE CASCADE,
  segment_id       bigint         NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
  -- values before closing, restored when the alert is resolved
  prev_condition    road_condition   NOT NULL,
  prev_cost         double precision NOT NULL,
  prev_reverse_cost double precision NOT NULL,
  closed_at        timestamptz    NOT NULL DEFAULT now(),
  PRIMARY KEY (alert_id, segment_id)
);
CREATE INDEX alert_closed_segments_segment_idx ON alert_closed_segments (segment_id);
