-- D4b (part 1) · F2 Road network (3 tables)
-- road_segments follows the pgRouting edge contract (id, source, target, cost,
-- reverse_cost). A negative cost removes that direction from the graph, so
-- closing a road for a hazard is a single UPDATE.

CREATE TABLE road_nodes (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  incident_id uuid   NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  geom        geometry(Point, 4326) NOT NULL
);
CREATE INDEX road_nodes_incident_idx ON road_nodes (incident_id);
CREATE INDEX road_nodes_geom_gix     ON road_nodes USING gist (geom);

CREATE TABLE road_segments (
  id                   bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  incident_id          uuid           NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  osm_way_id           bigint,
  source               bigint         NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
  target               bigint         NOT NULL REFERENCES road_nodes(id) ON DELETE CASCADE,
  geom                 geometry(LineString, 4326) NOT NULL,
  name                 text,
  road_class           road_class     NOT NULL DEFAULT 'RESIDENTIAL',
  width_m              numeric(5,2)   CHECK (width_m > 0),
  is_bridge            boolean        NOT NULL DEFAULT false,
  oneway               boolean        NOT NULL DEFAULT false,
  length_m             numeric(10,2)  NOT NULL CHECK (length_m >= 0),
  base_travel_s        numeric(10,2)  NOT NULL CHECK (base_travel_s >= 0),
  -- current state, cached from the latest road_condition_observations row
  condition            road_condition NOT NULL DEFAULT 'UNKNOWN',
  water_depth_cm       integer        CHECK (water_depth_cm >= 0),
  condition_confidence numeric(4,3)   CHECK (condition_confidence BETWEEN 0 AND 1),
  condition_updated_at timestamptz,
  -- effective routing weights (seconds); negative = closed (pgRouting convention)
  cost                 double precision NOT NULL,
  reverse_cost         double precision NOT NULL,
  CONSTRAINT road_segments_not_loop CHECK (source <> target),
  CONSTRAINT road_segments_oneway_reverse_closed CHECK (NOT oneway OR reverse_cost < 0)
);
CREATE INDEX road_segments_source_idx   ON road_segments (source);
CREATE INDEX road_segments_target_idx   ON road_segments (target);
CREATE INDEX road_segments_incident_idx ON road_segments (incident_id);
CREATE INDEX road_segments_geom_gix     ON road_segments USING gist (geom);
CREATE INDEX road_segments_closed_idx   ON road_segments (incident_id) WHERE cost < 0;

CREATE TABLE road_condition_observations (
  id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  segment_id         bigint         NOT NULL REFERENCES road_segments(id) ON DELETE CASCADE,
  condition          road_condition NOT NULL,
  water_depth_cm     integer        CHECK (water_depth_cm >= 0),
  confidence         numeric(4,3)   CHECK (confidence BETWEEN 0 AND 1),
  inference_run_id   uuid           REFERENCES inference_runs(id) ON DELETE SET NULL,
  reported_by        uuid           REFERENCES users(id),
  citizen_request_id uuid           REFERENCES citizen_requests(id) ON DELETE SET NULL,
  observed_at        timestamptz    NOT NULL DEFAULT now(),
  -- Exactly one source: AI, a responder, or a citizen.
  CONSTRAINT road_condition_observations_one_source
    CHECK (num_nonnulls(inference_run_id, reported_by, citizen_request_id) = 1)
);
CREATE INDEX road_condition_observations_segment_idx ON road_condition_observations (segment_id, observed_at DESC);

-- Keep the cached condition on road_segments in step with the newest observation.
-- (Routing cost itself is recalculated by the routing service / hazard engine.)
CREATE OR REPLACE FUNCTION apply_road_observation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  UPDATE road_segments
     SET condition            = NEW.condition,
         water_depth_cm       = NEW.water_depth_cm,
         condition_confidence = NEW.confidence,
         condition_updated_at = NEW.observed_at
   WHERE id = NEW.segment_id
     AND (condition_updated_at IS NULL OR condition_updated_at <= NEW.observed_at)
     AND condition <> 'HAZARD_CLOSED';   -- an active compound alert keeps the road closed
  RETURN NEW;
END $$;
CREATE TRIGGER road_condition_observations_apply AFTER INSERT ON road_condition_observations
  FOR EACH ROW EXECUTE FUNCTION apply_road_observation();
