-- D5 (part 1) · Citizens & Media (4 tables)
-- Created before the feature tables because hazards, road observations and
-- assistance cases can all originate from a citizen request.

CREATE TABLE citizens (
  id                 uuid        PRIMARY KEY DEFAULT uuidv7(),
  phone              text        NOT NULL UNIQUE,        -- verified by OTP; minimal personal data
  full_name          text,
  preferred_language text        NOT NULL DEFAULT 'ar',
  phone_verified_at  timestamptz,
  is_blocked         boolean     NOT NULL DEFAULT false,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE media_files (
  id                  uuid        PRIMARY KEY DEFAULT uuidv7(),
  storage_key         text        NOT NULL,
  mime_type           text        NOT NULL,
  sha256              text        NOT NULL,
  uploaded_by_user    uuid        REFERENCES users(id) ON DELETE SET NULL,
  uploaded_by_citizen uuid        REFERENCES citizens(id) ON DELETE SET NULL,
  created_at          timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT media_files_one_uploader CHECK (num_nonnulls(uploaded_by_user, uploaded_by_citizen) <= 1)
);
CREATE INDEX media_files_sha256_idx ON media_files (sha256);

CREATE TABLE citizen_requests (
  id                  uuid                   PRIMARY KEY DEFAULT uuidv7(),
  citizen_id          uuid                   NOT NULL REFERENCES citizens(id) ON DELETE CASCADE,
  incident_id         uuid                   REFERENCES incidents(id) ON DELETE SET NULL,
  request_type        citizen_request_type   NOT NULL,
  location            geometry(Point, 4326)  NOT NULL,
  location_accuracy_m numeric(7,2)           CHECK (location_accuracy_m >= 0),
  people_count        smallint               CHECK (people_count > 0),
  description         text,
  status              citizen_request_status NOT NULL DEFAULT 'RECEIVED',
  duplicate_of_id     uuid                   REFERENCES citizen_requests(id) ON DELETE SET NULL,
  verified_by         uuid                   REFERENCES users(id),
  verified_at         timestamptz,
  created_at          timestamptz            NOT NULL DEFAULT now(),
  CONSTRAINT citizen_requests_duplicate_has_original CHECK ((status = 'DUPLICATE') = (duplicate_of_id IS NOT NULL)),
  CONSTRAINT citizen_requests_not_own_duplicate      CHECK (duplicate_of_id IS DISTINCT FROM id)
);
CREATE INDEX citizen_requests_incident_status_idx ON citizen_requests (incident_id, status);
CREATE INDEX citizen_requests_location_gix         ON citizen_requests USING gist (location);
CREATE INDEX citizen_requests_citizen_idx         ON citizen_requests (citizen_id);

-- Auto-match a new request to the active incident whose area contains it.
CREATE OR REPLACE FUNCTION match_citizen_request_incident() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.incident_id IS NULL THEN
    SELECT i.id INTO NEW.incident_id
    FROM incidents i
    WHERE i.status <> 'CLOSED' AND NOT i.is_historical
      AND ST_Contains(i.area, NEW.location)
    ORDER BY i.started_at DESC
    LIMIT 1;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER citizen_requests_match_incident BEFORE INSERT ON citizen_requests
  FOR EACH ROW EXECUTE FUNCTION match_citizen_request_incident();

CREATE TABLE citizen_request_media (
  request_id uuid NOT NULL REFERENCES citizen_requests(id) ON DELETE CASCADE,
  media_id   uuid NOT NULL REFERENCES media_files(id) ON DELETE CASCADE,
  PRIMARY KEY (request_id, media_id)
);
CREATE INDEX citizen_request_media_media_idx ON citizen_request_media (media_id);
