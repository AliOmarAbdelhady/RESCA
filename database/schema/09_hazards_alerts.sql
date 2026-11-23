-- D4d · F5 Hazards & Compound Hazard Alerts (5 tables; alert_closed_segments is in 10_routing.sql)
-- Individual hazards + infrastructure feed a data-driven rule engine. When two
-- interact in space (e.g. floodwater within 30 m of an energized power line =
-- "Electrified Water"), a compound alert opens a no-entry zone, closes roads,
-- invalidates routes and warns responders.

CREATE TABLE infrastructure_assets (
  id               uuid        PRIMARY KEY DEFAULT uuidv7(),
  incident_id      uuid        NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  asset_type       asset_type  NOT NULL,
  geom             geometry(Geometry, 4326) NOT NULL,
  voltage_kv       numeric(7,2) CHECK (voltage_kv >= 0),
  operator         text,
  power_state      power_state NOT NULL DEFAULT 'UNKNOWN',
  state_updated_at timestamptz
);
CREATE INDEX infrastructure_assets_incident_idx ON infrastructure_assets (incident_id, asset_type);
CREATE INDEX infrastructure_assets_geom_gix     ON infrastructure_assets USING gist (geom);

CREATE TABLE hazards (
  id                 uuid          PRIMARY KEY DEFAULT uuidv7(),
  incident_id        uuid          NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  hazard_type        hazard_type   NOT NULL,
  geom               geometry(Geometry, 4326) NOT NULL,
  severity           smallint      NOT NULL CHECK (severity BETWEEN 1 AND 5),
  confidence         numeric(4,3)  CHECK (confidence BETWEEN 0 AND 1),
  origin             hazard_origin NOT NULL,          -- observed vs inferred kept distinct
  inference_run_id   uuid          REFERENCES inference_runs(id) ON DELETE SET NULL,
  reported_by        uuid          REFERENCES users(id),
  citizen_request_id uuid          REFERENCES citizen_requests(id) ON DELETE SET NULL,
  status             hazard_status NOT NULL DEFAULT 'SUSPECTED',
  attributes         jsonb         NOT NULL DEFAULT '{}',   -- {"water_depth_cm": 40}
  observed_at        timestamptz   NOT NULL DEFAULT now(),
  expires_at         timestamptz,
  CONSTRAINT hazards_one_source CHECK (num_nonnulls(inference_run_id, reported_by, citizen_request_id) = 1),
  CONSTRAINT hazards_origin_matches_source CHECK (
       (origin = 'AI_DETECTED'        AND inference_run_id   IS NOT NULL)
    OR (origin = 'RESPONDER_REPORTED' AND reported_by        IS NOT NULL)
    OR (origin = 'CITIZEN_REPORTED'   AND citizen_request_id IS NOT NULL))
);
CREATE INDEX hazards_live_idx ON hazards (incident_id, hazard_type) WHERE status IN ('SUSPECTED', 'CONFIRMED');
CREATE INDEX hazards_geom_gix ON hazards USING gist (geom);

CREATE TABLE hazard_rules (
  id                  uuid         PRIMARY KEY DEFAULT uuidv7(),
  code                text         NOT NULL UNIQUE,   -- "ELECTRIFIED_WATER"
  name                text         NOT NULL,
  description         text         NOT NULL,
  primary_hazard_type hazard_type  NOT NULL,
  secondary_kind      rule_operand NOT NULL,          -- HAZARD | ASSET | ROAD
  secondary_types     text[]       NOT NULL,          -- {"POWER_LINE","TRANSFORMER"}
  max_distance_m      numeric(7,2) NOT NULL CHECK (max_distance_m >= 0),
  danger_buffer_m     numeric(7,2) NOT NULL CHECK (danger_buffer_m >= 0),
  resulting_severity  smallint     NOT NULL CHECK (resulting_severity BETWEEN 1 AND 5),
  closes_roads        boolean      NOT NULL DEFAULT true,
  warning_template    text         NOT NULL,          -- "Electrified water near {street}. Do NOT enter."
  is_active           boolean      NOT NULL DEFAULT true
);

CREATE TABLE compound_alerts (
  id              uuid         PRIMARY KEY DEFAULT uuidv7(),
  incident_id     uuid         NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  rule_id         uuid         NOT NULL REFERENCES hazard_rules(id),
  title           text         NOT NULL,
  danger_zone     geometry(MultiPolygon, 4326) NOT NULL,
  severity        smallint     NOT NULL CHECK (severity BETWEEN 1 AND 5),
  status          alert_status NOT NULL DEFAULT 'ACTIVE',
  triggered_at    timestamptz  NOT NULL DEFAULT now(),
  acknowledged_by uuid         REFERENCES users(id),
  acknowledged_at timestamptz,
  resolved_by     uuid         REFERENCES users(id),
  resolved_at     timestamptz,
  resolution_note text,
  CONSTRAINT compound_alerts_resolution CHECK ((status IN ('RESOLVED', 'FALSE_ALARM')) = (resolved_at IS NOT NULL))
);
CREATE INDEX compound_alerts_active_idx ON compound_alerts (incident_id) WHERE status IN ('ACTIVE', 'ACKNOWLEDGED');
CREATE INDEX compound_alerts_zone_gix   ON compound_alerts USING gist (danger_zone);

CREATE TABLE compound_alert_sources (
  id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  alert_id  uuid NOT NULL REFERENCES compound_alerts(id) ON DELETE CASCADE,
  hazard_id uuid REFERENCES hazards(id) ON DELETE CASCADE,
  asset_id  uuid REFERENCES infrastructure_assets(id) ON DELETE CASCADE,
  CONSTRAINT compound_alert_sources_hazard_xor_asset CHECK (num_nonnulls(hazard_id, asset_id) = 1)
);
CREATE UNIQUE INDEX compound_alert_sources_hazard_uq ON compound_alert_sources (alert_id, hazard_id) WHERE hazard_id IS NOT NULL;
CREATE UNIQUE INDEX compound_alert_sources_asset_uq  ON compound_alert_sources (alert_id, asset_id)  WHERE asset_id  IS NOT NULL;
CREATE INDEX compound_alert_sources_hazard_idx ON compound_alert_sources (hazard_id);
CREATE INDEX compound_alert_sources_asset_idx  ON compound_alert_sources (asset_id);
