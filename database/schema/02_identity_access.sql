-- D1 · Identity & Access (10 tables)
-- Users are classified on two axes: WHICH agency (Government/Police/EMS/Fire)
-- and WHAT role. Only the Platform Admin has no agency.

CREATE TABLE agencies (
  id               uuid PRIMARY KEY DEFAULT uuidv7(),
  name             text        NOT NULL,
  agency_type      agency_type NOT NULL,
  parent_agency_id uuid        REFERENCES agencies(id) ON DELETE SET NULL,
  jurisdiction     geometry(MultiPolygon, 4326),
  phone            text,
  is_active        boolean     NOT NULL DEFAULT true,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT agencies_name_uq UNIQUE (name),
  CONSTRAINT agencies_not_own_parent CHECK (parent_agency_id IS DISTINCT FROM id)
);
CREATE INDEX agencies_parent_idx       ON agencies (parent_agency_id);
CREATE INDEX agencies_jurisdiction_gix ON agencies USING gist (jurisdiction);
CREATE TRIGGER agencies_updated_at BEFORE UPDATE ON agencies FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE roles (
  code  text       PRIMARY KEY,
  name  text       NOT NULL,
  scope role_scope NOT NULL
);

CREATE TABLE permissions (
  code        text PRIMARY KEY,
  description text NOT NULL
);

CREATE TABLE role_permissions (
  role_code       text NOT NULL REFERENCES roles(code) ON DELETE CASCADE,
  permission_code text NOT NULL REFERENCES permissions(code) ON DELETE CASCADE,
  PRIMARY KEY (role_code, permission_code)
);
CREATE INDEX role_permissions_permission_idx ON role_permissions (permission_code);

CREATE TABLE users (
  id            uuid        PRIMARY KEY DEFAULT uuidv7(),
  agency_id     uuid        REFERENCES agencies(id) ON DELETE RESTRICT,
  role_code     text        NOT NULL REFERENCES roles(code),
  full_name     text        NOT NULL,
  email         citext      NOT NULL UNIQUE,
  phone         text,
  password_hash text        NOT NULL,
  job_title     text,                       -- display only: "Paramedic", "Fire Captain"
  badge_number  text,
  status        user_status NOT NULL DEFAULT 'INVITED',
  last_login_at timestamptz,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now(),
  deleted_at    timestamptz,
  -- Platform Admin is the only user without an agency.
  CONSTRAINT users_platform_admin_has_no_agency
    CHECK ((role_code = 'PLATFORM_ADMIN') = (agency_id IS NULL))
);
CREATE INDEX users_agency_idx ON users (agency_id) WHERE deleted_at IS NULL;
CREATE INDEX users_role_idx   ON users (role_code);
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TABLE user_sessions (
  id                 uuid        PRIMARY KEY DEFAULT uuidv7(),
  user_id            uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  refresh_token_hash text        NOT NULL UNIQUE,
  device_info        text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  expires_at         timestamptz NOT NULL,
  revoked_at         timestamptz,
  CONSTRAINT user_sessions_expiry_after_creation CHECK (expires_at > created_at)
);
CREATE INDEX user_sessions_user_active_idx ON user_sessions (user_id) WHERE revoked_at IS NULL;

CREATE TABLE user_devices (
  id           uuid            PRIMARY KEY DEFAULT uuidv7(),
  user_id      uuid            NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform     device_platform NOT NULL,
  push_token   text            NOT NULL UNIQUE,
  last_seen_at timestamptz     NOT NULL DEFAULT now()
);
CREATE INDEX user_devices_user_idx ON user_devices (user_id);

CREATE TABLE teams (
  id         uuid        PRIMARY KEY DEFAULT uuidv7(),
  agency_id  uuid        NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  name       text        NOT NULL,
  team_type  team_type   NOT NULL,
  home_base  geometry(Point, 4326),
  status     team_status NOT NULL DEFAULT 'AVAILABLE',
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT teams_agency_name_uq UNIQUE (agency_id, name)
);
CREATE INDEX teams_home_base_gix ON teams USING gist (home_base);

CREATE TABLE team_members (
  id        uuid        PRIMARY KEY DEFAULT uuidv7(),
  team_id   uuid        NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  user_id   uuid        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  is_leader boolean     NOT NULL DEFAULT false,
  joined_at timestamptz NOT NULL DEFAULT now(),
  left_at   timestamptz,
  CONSTRAINT team_members_left_after_joined CHECK (left_at IS NULL OR left_at >= joined_at)
);
-- ICS unity of command: one active team per responder.
CREATE UNIQUE INDEX team_members_one_active_team_uq ON team_members (user_id) WHERE left_at IS NULL;
CREATE INDEX team_members_team_idx ON team_members (team_id) WHERE left_at IS NULL;

CREATE TABLE vehicles (
  id                 uuid           PRIMARY KEY DEFAULT uuidv7(),
  agency_id          uuid           NOT NULL REFERENCES agencies(id) ON DELETE CASCADE,
  team_id            uuid           REFERENCES teams(id) ON DELETE SET NULL,
  call_sign          text           NOT NULL,
  vehicle_type       vehicle_type   NOT NULL,
  plate_number       text,
  max_water_depth_cm integer        CHECK (max_water_depth_cm >= 0),  -- feeds routing: can it cross floodwater?
  status             vehicle_status NOT NULL DEFAULT 'AVAILABLE',
  CONSTRAINT vehicles_agency_call_sign_uq UNIQUE (agency_id, call_sign)
);
CREATE INDEX vehicles_team_idx ON vehicles (team_id);
