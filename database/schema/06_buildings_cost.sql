-- D4a · F1 Buildings, Damage & Restoration Cost (6 tables)
-- cost = floor_area_m2 × unit_rate(occupancy, construction) × repair_ratio(damage_grade)
-- reported as a low–high range with every assumption recorded.

CREATE TABLE buildings (
  id            uuid              PRIMARY KEY DEFAULT uuidv7(),
  incident_id   uuid              NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
  external_ref  text,                                         -- OSM / Overture id
  footprint     geometry(Polygon, 4326) NOT NULL,
  area_m2       numeric GENERATED ALWAYS AS (ST_Area(footprint::geography)) STORED,
  floors        smallint          CHECK (floors > 0),
  height_m      numeric(6,2)      CHECK (height_m > 0),
  occupancy     occupancy_type    NOT NULL DEFAULT 'UNKNOWN',
  construction  construction_type NOT NULL DEFAULT 'UNKNOWN',
  est_occupants integer           CHECK (est_occupants >= 0),
  address       text,
  source        building_source   NOT NULL,
  created_at    timestamptz       NOT NULL DEFAULT now(),
  CONSTRAINT buildings_incident_external_ref_uq UNIQUE (incident_id, external_ref)
);
CREATE INDEX buildings_incident_idx   ON buildings (incident_id);
CREATE INDEX buildings_footprint_gix  ON buildings USING gist (footprint);

CREATE TABLE building_assessments (
  id               uuid              PRIMARY KEY DEFAULT uuidv7(),
  building_id      uuid              NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
  inference_run_id uuid              REFERENCES inference_runs(id) ON DELETE SET NULL,
  assessed_by      uuid              REFERENCES users(id),
  method           assessment_method NOT NULL,
  damage_grade     damage_grade      NOT NULL,
  p_no_damage      numeric(4,3)      CHECK (p_no_damage BETWEEN 0 AND 1),
  p_minor          numeric(4,3)      CHECK (p_minor     BETWEEN 0 AND 1),
  p_major          numeric(4,3)      CHECK (p_major     BETWEEN 0 AND 1),
  p_destroyed      numeric(4,3)      CHECK (p_destroyed BETWEEN 0 AND 1),
  pre_image_id     uuid              REFERENCES images(id) ON DELETE SET NULL,
  post_image_id    uuid              REFERENCES images(id) ON DELETE SET NULL,
  review_status    review_status     NOT NULL DEFAULT 'PENDING',
  reviewed_by      uuid              REFERENCES users(id),
  reviewed_at      timestamptz,
  is_current       boolean           NOT NULL DEFAULT true,
  created_at       timestamptz       NOT NULL DEFAULT now(),
  -- Every verdict comes from an AI run or from a named person.
  CONSTRAINT building_assessments_has_source CHECK (inference_run_id IS NOT NULL OR assessed_by IS NOT NULL),
  -- AI verdicts carry a full probability distribution that sums to ~1.
  CONSTRAINT building_assessments_probabilities CHECK (
    method = 'FIELD_INSPECTION'
    OR (num_nonnulls(p_no_damage, p_minor, p_major, p_destroyed) = 4
        AND abs(p_no_damage + p_minor + p_major + p_destroyed - 1) <= 0.01)),
  CONSTRAINT building_assessments_review_complete CHECK ((review_status = 'PENDING') = (reviewed_at IS NULL))
);
-- Exactly one current verdict per building; history is kept.
CREATE UNIQUE INDEX building_assessments_one_current_uq ON building_assessments (building_id) WHERE is_current;
CREATE INDEX building_assessments_run_idx     ON building_assessments (inference_run_id);
CREATE INDEX building_assessments_pending_idx ON building_assessments (review_status) WHERE review_status = 'PENDING';

-- A new current verdict retires the previous one.
CREATE OR REPLACE FUNCTION retire_previous_assessment() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.is_current THEN
    UPDATE building_assessments
       SET is_current = false
     WHERE building_id = NEW.building_id AND is_current AND id <> NEW.id;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER building_assessments_retire_previous BEFORE INSERT ON building_assessments
  FOR EACH ROW EXECUTE FUNCTION retire_previous_assessment();

CREATE TABLE cost_profiles (
  id         uuid    PRIMARY KEY DEFAULT uuidv7(),
  name       text    NOT NULL UNIQUE,     -- "Egypt 2026 urban"
  region     text    NOT NULL,
  currency   char(3) NOT NULL,            -- ISO 4217
  source     text    NOT NULL,            -- "FEMA HAZUS ratios + local unit rates"
  valid_from date    NOT NULL
);

CREATE TABLE cost_profile_unit_rates (
  profile_id       uuid              NOT NULL REFERENCES cost_profiles(id) ON DELETE CASCADE,
  occupancy        occupancy_type    NOT NULL,
  construction     construction_type NOT NULL,
  cost_per_m2_low  numeric(12,2)     NOT NULL CHECK (cost_per_m2_low >= 0),
  cost_per_m2_high numeric(12,2)     NOT NULL,
  PRIMARY KEY (profile_id, occupancy, construction),
  CONSTRAINT cost_profile_unit_rates_range CHECK (cost_per_m2_high >= cost_per_m2_low)
);

CREATE TABLE cost_profile_repair_ratios (
  profile_id   uuid         NOT NULL REFERENCES cost_profiles(id) ON DELETE CASCADE,
  damage_grade damage_grade NOT NULL,
  ratio_low    numeric(4,3) NOT NULL CHECK (ratio_low BETWEEN 0 AND 1),
  ratio_high   numeric(4,3) NOT NULL CHECK (ratio_high BETWEEN 0 AND 1),
  PRIMARY KEY (profile_id, damage_grade),
  CONSTRAINT cost_profile_repair_ratios_range CHECK (ratio_high >= ratio_low)
);

-- Snapshot table: a published report never changes when rates are edited later.
CREATE TABLE cost_estimates (
  id                uuid          PRIMARY KEY DEFAULT uuidv7(),
  building_id       uuid          NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
  assessment_id     uuid          NOT NULL REFERENCES building_assessments(id) ON DELETE CASCADE,
  cost_profile_id   uuid          NOT NULL REFERENCES cost_profiles(id),
  floor_area_m2     numeric(12,2) NOT NULL CHECK (floor_area_m2 >= 0),
  repair_ratio_low  numeric(4,3)  NOT NULL,
  repair_ratio_high numeric(4,3)  NOT NULL,
  cost_low          numeric(14,2) NOT NULL CHECK (cost_low >= 0),
  cost_high         numeric(14,2) NOT NULL,
  currency          char(3)       NOT NULL,
  assumptions       jsonb         NOT NULL DEFAULT '{}',   -- {"floors":"defaulted to 3"}
  computed_at       timestamptz   NOT NULL DEFAULT now(),
  CONSTRAINT cost_estimates_range CHECK (cost_high >= cost_low)
);
CREATE INDEX cost_estimates_building_idx   ON cost_estimates (building_id, computed_at DESC);
CREATE INDEX cost_estimates_assessment_idx ON cost_estimates (assessment_id);
CREATE INDEX cost_estimates_profile_idx    ON cost_estimates (cost_profile_id);
