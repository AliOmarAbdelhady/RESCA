-- RescueVision database: extensions
-- Target: PostgreSQL 18 + PostGIS 3.6 + pgRouting 4 + pgvector 0.8

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- PostgreSQL 18 ships uuidv7() natively: time-ordered ids that index well
-- and can be generated offline by the mobile app.
DO $$
BEGIN
  IF current_setting('server_version_num')::int < 180000 THEN
    RAISE EXCEPTION 'RescueVision requires PostgreSQL 18+ (uuidv7). Found %', version();
  END IF;
END $$;

-- Shared trigger: keep updated_at current on every UPDATE.
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END $$;
