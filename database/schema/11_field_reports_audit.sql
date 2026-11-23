-- D5 (part 2) · Field channel, notifications, reports, similar cases, audit (8 tables)

-- Live responder GPS: very high volume, append-only → monthly range partitions.
CREATE TABLE responder_positions (
  id          bigint GENERATED ALWAYS AS IDENTITY,
  user_id     uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  incident_id uuid        REFERENCES incidents(id) ON DELETE SET NULL,
  mission_id  uuid        REFERENCES missions(id) ON DELETE SET NULL,
  recorded_at timestamptz NOT NULL,
  geom        geometry(Point, 4326) NOT NULL,
  accuracy_m  numeric(7,2) NOT NULL CHECK (accuracy_m >= 0),
  speed_mps   numeric(6,2) CHECK (speed_mps >= 0),
  heading_deg numeric(5,2) CHECK (heading_deg >= 0 AND heading_deg < 360),
  battery_pct smallint     CHECK (battery_pct BETWEEN 0 AND 100),
  PRIMARY KEY (id, recorded_at)          -- partition key must be part of the PK
) PARTITION BY RANGE (recorded_at);
CREATE INDEX responder_positions_time_brin ON responder_positions USING brin (recorded_at);
CREATE INDEX responder_positions_user_idx  ON responder_positions (user_id, recorded_at DESC);
CREATE INDEX responder_positions_geom_gix  ON responder_positions USING gist (geom);

-- One row per responder, UPSERTed on every ping: the live map reads only this.
CREATE TABLE responder_last_positions (
  user_id     uuid        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  geom        geometry(Point, 4326) NOT NULL,
  accuracy_m  numeric(7,2) NOT NULL,
  recorded_at timestamptz NOT NULL,
  incident_id uuid        REFERENCES incidents(id) ON DELETE SET NULL,
  mission_id  uuid        REFERENCES missions(id) ON DELETE SET NULL
);
CREATE INDEX responder_last_positions_geom_gix ON responder_last_positions USING gist (geom);

CREATE OR REPLACE FUNCTION upsert_last_position() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  INSERT INTO responder_last_positions AS r (user_id, geom, accuracy_m, recorded_at, incident_id, mission_id)
  VALUES (NEW.user_id, NEW.geom, NEW.accuracy_m, NEW.recorded_at, NEW.incident_id, NEW.mission_id)
  ON CONFLICT (user_id) DO UPDATE
     SET geom = EXCLUDED.geom, accuracy_m = EXCLUDED.accuracy_m, recorded_at = EXCLUDED.recorded_at,
         incident_id = EXCLUDED.incident_id, mission_id = EXCLUDED.mission_id
   WHERE r.recorded_at <= EXCLUDED.recorded_at;   -- late, out-of-order pings never move the marker back
  RETURN NEW;
END $$;
CREATE TRIGGER responder_positions_last AFTER INSERT ON responder_positions
  FOR EACH ROW EXECUTE FUNCTION upsert_last_position();

CREATE TABLE sos_alerts (
  id              uuid        PRIMARY KEY DEFAULT uuidv7(),
  incident_id     uuid        NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  user_id         uuid        NOT NULL REFERENCES users(id),
  location        geometry(Point, 4326) NOT NULL,
  message         text,
  media_id        uuid        REFERENCES media_files(id) ON DELETE SET NULL,
  status          sos_status  NOT NULL DEFAULT 'TRIGGERED',
  triggered_at    timestamptz NOT NULL DEFAULT now(),
  acknowledged_by uuid        REFERENCES users(id),
  acknowledged_at timestamptz,
  resolved_at     timestamptz,
  CONSTRAINT sos_alerts_ack_complete      CHECK (status = 'TRIGGERED' OR acknowledged_at IS NOT NULL),
  CONSTRAINT sos_alerts_resolved_complete CHECK ((status = 'RESOLVED') = (resolved_at IS NOT NULL))
);
CREATE INDEX sos_alerts_open_idx     ON sos_alerts (incident_id) WHERE status <> 'RESOLVED';
CREATE INDEX sos_alerts_location_gix ON sos_alerts USING gist (location);

CREATE TABLE notifications (
  id           uuid              PRIMARY KEY DEFAULT uuidv7(),
  user_id      uuid              NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  incident_id  uuid              REFERENCES incidents(id) ON DELETE CASCADE,
  kind         notification_kind NOT NULL,
  title        text              NOT NULL,
  body         text              NOT NULL,
  severity     smallint          NOT NULL DEFAULT 3 CHECK (severity BETWEEN 1 AND 5),
  -- typed links instead of a polymorphic (type, id) pair, so FKs stay enforced
  alert_id     uuid              REFERENCES compound_alerts(id) ON DELETE CASCADE,
  mission_id   uuid              REFERENCES missions(id) ON DELETE CASCADE,
  case_id      uuid              REFERENCES assistance_cases(id) ON DELETE CASCADE,
  sos_id       uuid              REFERENCES sos_alerts(id) ON DELETE CASCADE,
  route_id     uuid              REFERENCES routes(id) ON DELETE CASCADE,
  created_at   timestamptz       NOT NULL DEFAULT now(),
  delivered_at timestamptz,
  read_at      timestamptz,
  CONSTRAINT notifications_one_subject CHECK (num_nonnulls(alert_id, mission_id, case_id, sos_id, route_id) <= 1)
);
CREATE INDEX notifications_unread_idx ON notifications (user_id, created_at DESC) WHERE read_at IS NULL;

CREATE TABLE reports (
  id               uuid          PRIMARY KEY DEFAULT uuidv7(),
  incident_id      uuid          NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  report_type      report_type   NOT NULL,
  title            text          NOT NULL,
  period_from      timestamptz,
  period_to        timestamptz,
  scope_zone_id    uuid          REFERENCES zones(id) ON DELETE SET NULL,
  status           report_status NOT NULL DEFAULT 'DRAFT',
  stats_snapshot   jsonb         NOT NULL DEFAULT '{}',   -- numbers frozen at generation
  pdf_storage_key  text,
  html_storage_key text,
  job_id           uuid          REFERENCES processing_jobs(id) ON DELETE SET NULL,
  generated_by     uuid          REFERENCES users(id),
  approved_by      uuid          REFERENCES users(id),
  approved_at      timestamptz,
  created_at       timestamptz   NOT NULL DEFAULT now(),
  disclaimer       text          NOT NULL DEFAULT 'AI decision-support output; human review required.',
  CONSTRAINT reports_period CHECK (period_to IS NULL OR period_from IS NULL OR period_to >= period_from),
  CONSTRAINT reports_approval CHECK ((status IN ('APPROVED', 'PUBLISHED')) = (approved_at IS NOT NULL AND approved_by IS NOT NULL))
);
CREATE INDEX reports_incident_idx ON reports (incident_id, created_at DESC);

CREATE TABLE report_shares (
  report_id uuid        NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
  agency_id uuid        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  shared_by uuid        REFERENCES users(id),
  shared_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (report_id, agency_id)
);
CREATE INDEX report_shares_agency_idx ON report_shares (agency_id);

-- Similar past cases: DINOv2 embeddings (768 dims) with HNSW cosine search.
-- Query as: ORDER BY embedding <=> $1 LIMIT k  (so the index is used).
CREATE TABLE image_embeddings (
  id          uuid             PRIMARY KEY DEFAULT uuidv7(),
  model_id    uuid             NOT NULL REFERENCES ai_models(id),
  incident_id uuid             NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  source_kind embedding_source NOT NULL,
  building_id uuid             REFERENCES buildings(id) ON DELETE CASCADE,
  image_id    uuid             REFERENCES images(id) ON DELETE CASCADE,
  embedding   vector(768)      NOT NULL,
  created_at  timestamptz      NOT NULL DEFAULT now(),
  CONSTRAINT image_embeddings_source_link CHECK (
       (source_kind = 'BUILDING_CROP' AND building_id IS NOT NULL)
    OR (source_kind = 'SCENE_TILE'    AND image_id    IS NOT NULL))
);
CREATE INDEX image_embeddings_hnsw ON image_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX image_embeddings_incident_idx ON image_embeddings (incident_id);

-- Accountability: who changed what, partitioned by month.
CREATE TABLE audit_log (
  id            bigint GENERATED ALWAYS AS IDENTITY,
  actor_user_id uuid,                      -- no FK: the trail must survive user deletion
  action        text        NOT NULL,      -- INSERT / UPDATE / DELETE / LOGIN / APPROVE …
  entity_table  text        NOT NULL,
  entity_id     text,
  before        jsonb,
  after         jsonb,
  ip            inet,
  created_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);
CREATE INDEX audit_log_time_brin  ON audit_log USING brin (created_at);
CREATE INDEX audit_log_entity_idx ON audit_log (entity_table, entity_id);

-- Partition helper: create monthly partitions for a range-partitioned table.
CREATE OR REPLACE FUNCTION create_monthly_partitions(parent regclass, from_month date, months integer)
RETURNS void LANGUAGE plpgsql AS $$
DECLARE
  m date;
  part text;
BEGIN
  FOR i IN 0 .. months - 1 LOOP
    m := date_trunc('month', from_month)::date + make_interval(months => i);
    part := format('%s_%s', parent::text, to_char(m, 'YYYY_MM'));
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %s FOR VALUES FROM (%L) TO (%L)',
                   part, parent, m, (m + interval '1 month')::date);
  END LOOP;
END $$;

DO $$
BEGIN
  PERFORM create_monthly_partitions('responder_positions', date '2026-01-01', 24);
  PERFORM create_monthly_partitions('audit_log',           date '2026-01-01', 24);
END $$;
CREATE TABLE responder_positions_default PARTITION OF responder_positions DEFAULT;
CREATE TABLE audit_log_default           PARTITION OF audit_log DEFAULT;
