-- D3 · Imagery & AI Pipeline (6 tables)
-- Provenance backbone: every AI output row references inference_runs, so any
-- result can be traced to its model version and input imagery.
-- Image files live in MinIO; Postgres stores metadata and storage keys only.

CREATE TABLE capture_sessions (
  id            uuid           PRIMARY KEY DEFAULT uuidv7(),
  incident_id   uuid           NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  mission_id    uuid           REFERENCES missions(id) ON DELETE SET NULL,  -- the DRONE_SURVEY mission
  source_type   capture_source NOT NULL,
  phase         capture_phase  NOT NULL,                                    -- before/after axis of F1
  provider      text,                                                       -- "Maxar Open Data", "DJI Mavic 3T"
  captured_from timestamptz,
  captured_to   timestamptz,
  coverage      geometry(Polygon, 4326),
  uploaded_by   uuid           REFERENCES users(id),
  status        session_status NOT NULL DEFAULT 'UPLOADING',
  created_at    timestamptz    NOT NULL DEFAULT now(),
  CONSTRAINT capture_sessions_time_order CHECK (captured_to IS NULL OR captured_from IS NULL OR captured_to >= captured_from)
);
CREATE INDEX capture_sessions_incident_idx ON capture_sessions (incident_id, phase);
CREATE INDEX capture_sessions_coverage_gix ON capture_sessions USING gist (coverage);

CREATE TABLE images (
  id              uuid          PRIMARY KEY DEFAULT uuidv7(),
  session_id      uuid          NOT NULL REFERENCES capture_sessions(id) ON DELETE CASCADE,
  media_kind      media_kind    NOT NULL DEFAULT 'PHOTO',
  frame_index     integer       CHECK (frame_index >= 0),
  storage_key     text          NOT NULL,
  sha256          text          NOT NULL UNIQUE,      -- the same photo is never stored twice
  width_px        integer       NOT NULL CHECK (width_px > 0),
  height_px       integer       NOT NULL CHECK (height_px > 0),
  spectral_band   spectral_band NOT NULL DEFAULT 'RGB',
  captured_at     timestamptz,
  camera_position geometry(PointZ, 4326),
  altitude_agl_m  numeric(7,2),
  gimbal_pitch    numeric(6,2),
  gimbal_yaw      numeric(6,2),
  gimbal_roll     numeric(6,2),
  gsd_cm          numeric(7,2)  CHECK (gsd_cm > 0),   -- gates person detection at high altitude
  gps_accuracy_m  numeric(7,2)  CHECK (gps_accuracy_m >= 0),
  footprint       geometry(Polygon, 4326),
  exif            jsonb,
  CONSTRAINT images_frame_index_for_video CHECK ((media_kind = 'VIDEO_FRAME') = (frame_index IS NOT NULL))
);
CREATE INDEX images_session_idx    ON images (session_id, captured_at);
CREATE INDEX images_footprint_gix  ON images USING gist (footprint);
CREATE INDEX images_camera_gix     ON images USING gist (camera_position);

CREATE TABLE ai_models (
  id                uuid       PRIMARY KEY DEFAULT uuidv7(),
  name              text       NOT NULL,
  version           text       NOT NULL,
  task              model_task NOT NULL,
  architecture      text       NOT NULL,            -- "YOLOv8s", "DINOv2 + MLP"
  training_datasets text[]     NOT NULL DEFAULT '{}',
  metrics           jsonb,
  weights_uri       text,
  is_active         boolean    NOT NULL DEFAULT false,
  created_at        timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT ai_models_name_version_uq UNIQUE (name, version)
);
-- One active model per task.
CREATE UNIQUE INDEX ai_models_one_active_per_task_uq ON ai_models (task) WHERE is_active;

CREATE TABLE processing_jobs (
  id            uuid        PRIMARY KEY DEFAULT uuidv7(),
  incident_id   uuid        NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  session_id    uuid        REFERENCES capture_sessions(id) ON DELETE SET NULL,
  job_type      job_type    NOT NULL,
  status        job_status  NOT NULL DEFAULT 'QUEUED',
  progress_pct  smallint    NOT NULL DEFAULT 0 CHECK (progress_pct BETWEEN 0 AND 100),
  error_message text,
  requested_by  uuid        REFERENCES users(id),
  queued_at     timestamptz NOT NULL DEFAULT now(),
  started_at    timestamptz,
  finished_at   timestamptz
);
CREATE INDEX processing_jobs_incident_idx ON processing_jobs (incident_id, queued_at DESC);
CREATE INDEX processing_jobs_open_idx     ON processing_jobs (status) WHERE status IN ('QUEUED', 'RUNNING');

-- raster_products and inference_runs reference each other (a run consumes
-- rasters and may produce masks), so the second FK is added after both exist.
CREATE TABLE raster_products (
  id                 uuid        PRIMARY KEY DEFAULT uuidv7(),
  session_id         uuid        NOT NULL REFERENCES capture_sessions(id) ON DELETE CASCADE,
  produced_by_run_id uuid,
  product_type       raster_type NOT NULL,
  storage_key        text        NOT NULL,
  resolution_m       numeric(8,3) CHECK (resolution_m > 0),
  bounds             geometry(Polygon, 4326) NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX raster_products_session_idx ON raster_products (session_id, product_type);
CREATE INDEX raster_products_bounds_gix  ON raster_products USING gist (bounds);

CREATE TABLE inference_runs (
  id             uuid       PRIMARY KEY DEFAULT uuidv7(),
  job_id         uuid       NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
  model_id       uuid       NOT NULL REFERENCES ai_models(id),
  pre_raster_id  uuid       REFERENCES raster_products(id),   -- set for before/after models
  post_raster_id uuid       NOT NULL REFERENCES raster_products(id),
  params         jsonb      NOT NULL DEFAULT '{}',
  status         job_status NOT NULL DEFAULT 'QUEUED',
  started_at     timestamptz,
  finished_at    timestamptz,
  CONSTRAINT inference_runs_pre_differs_from_post CHECK (pre_raster_id IS DISTINCT FROM post_raster_id)
);
CREATE INDEX inference_runs_job_idx   ON inference_runs (job_id);
CREATE INDEX inference_runs_model_idx ON inference_runs (model_id);

ALTER TABLE raster_products
  ADD CONSTRAINT raster_products_produced_by_run_fk
  FOREIGN KEY (produced_by_run_id) REFERENCES inference_runs(id) ON DELETE SET NULL;
CREATE INDEX raster_products_run_idx ON raster_products (produced_by_run_id);
