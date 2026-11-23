-- Self-checks run by build.sh. Each block raises an exception on failure,
-- so a broken schema stops the build (psql ON_ERROR_STOP).

-- 1. Table count matches the design (56 logical tables, partitions excluded).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
  WHERE ns.nspname = 'public' AND c.relkind IN ('r','p') AND NOT c.relispartition
    AND c.relname <> 'spatial_ref_sys';
  IF n <> 56 THEN RAISE EXCEPTION 'expected 56 tables, found %', n; END IF;
END $$;

-- 2. Every geometry column has a GiST index.
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(f_table_name || '.' || f_geometry_column, ', ') INTO missing
  FROM geometry_columns g
  WHERE f_table_schema = 'public'
    AND EXISTS (SELECT 1 FROM pg_class r WHERE r.relname = g.f_table_name
                AND r.relkind IN ('r', 'p') AND NOT r.relispartition)   -- tables only, not views/partitions
    AND NOT EXISTS (
      SELECT 1 FROM pg_index i
      JOIN pg_class t  ON t.oid = i.indrelid
      JOIN pg_class ix ON ix.oid = i.indexrelid
      JOIN pg_am am    ON am.oid = ix.relam
      JOIN pg_attribute att ON att.attrelid = t.oid AND att.attnum = ANY (i.indkey)
      WHERE t.relname = g.f_table_name AND att.attname = g.f_geometry_column AND am.amname = 'gist');
  IF missing IS NOT NULL THEN RAISE EXCEPTION 'geometry columns without GiST index: %', missing; END IF;
END $$;

-- 3. Report foreign-key columns that have no index starting with them (informational).
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(c.conrelid::regclass || '(' || a.attname || ')', ', ' ORDER BY 1) INTO missing
  FROM pg_constraint c
  JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
  JOIN pg_class t ON t.oid = c.conrelid
  WHERE c.contype = 'f' AND array_length(c.conkey, 1) = 1 AND NOT t.relispartition
    AND NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = c.conrelid AND i.indkey[0] = c.conkey[1]);
  IF missing IS NOT NULL THEN RAISE NOTICE 'FK columns without a leading index: %', missing; END IF;
END $$;

-- 4. Platform-admin rule is enforced.
DO $$
BEGIN
  BEGIN
    INSERT INTO users (agency_id, role_code, full_name, email, password_hash)
    VALUES (NULL, 'COMMANDER', 'x', 'should-fail@test.local', 'x');
    RAISE EXCEPTION 'CHECK users_platform_admin_has_no_agency did not fire';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

-- 5. Mission assignment must target a team XOR a user.
DO $$
DECLARE m uuid;
BEGIN
  SELECT id INTO m FROM missions LIMIT 1;
  IF m IS NULL THEN RETURN; END IF;   -- reference-only build
  BEGIN
    INSERT INTO mission_assignments (mission_id) VALUES (m);
    RAISE EXCEPTION 'CHECK mission_assignments_team_xor_user did not fire';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

-- 6. Demo scenario: Electrified Water fired, closed El-Nile Street and cut the route.
DO $$
DECLARE inc uuid; n_alert int; n_closed int; n_invalid int; n_notified int; n_reopened int; a uuid;
BEGIN
  SELECT id INTO inc FROM incidents WHERE code = 'INC-2026-0001';
  IF inc IS NULL THEN RETURN; END IF;   -- reference-only build

  SELECT count(*), min(ca.id::text)::uuid INTO n_alert, a
  FROM compound_alerts ca JOIN hazard_rules r ON r.id = ca.rule_id
  WHERE ca.incident_id = inc AND r.code = 'ELECTRIFIED_WATER' AND ca.status = 'ACTIVE';
  IF n_alert <> 1 THEN RAISE EXCEPTION 'expected 1 Electrified Water alert, found %', n_alert; END IF;

  SELECT count(*) INTO n_closed FROM alert_closed_segments WHERE alert_id = a;
  IF n_closed = 0 THEN RAISE EXCEPTION 'Electrified Water alert closed no roads'; END IF;

  SELECT count(*) INTO n_invalid FROM routes WHERE invalidated_by_alert_id = a AND status = 'INVALIDATED';
  IF n_invalid <> 1 THEN RAISE EXCEPTION 'expected the rescue route to be invalidated, found %', n_invalid; END IF;

  SELECT count(*) INTO n_notified FROM notifications WHERE alert_id = a;
  IF n_notified = 0 THEN RAISE EXCEPTION 'no responder was warned'; END IF;

  IF NOT EXISTS (SELECT 1 FROM compound_alerts ca JOIN hazard_rules r ON r.id = ca.rule_id
                 WHERE ca.incident_id = inc AND r.code = 'COLLAPSE_ON_ROAD') THEN
    RAISE EXCEPTION 'Falling-Debris Zone alert did not fire';
  END IF;

  -- Re-running the engine must not duplicate alerts (idempotent).
  PERFORM evaluate_hazard_rules(inc);
  SELECT count(*) INTO n_alert FROM compound_alerts WHERE incident_id = inc;
  IF n_alert <> 2 THEN RAISE EXCEPTION 'rule engine is not idempotent: % alerts', n_alert; END IF;

  -- Resolving re-opens the street, then we roll back so the demo stays "live".
  BEGIN
    n_reopened := resolve_compound_alert(a, NULL, 'power cut by utility');
    IF n_reopened <> n_closed THEN RAISE EXCEPTION 'reopened % of % segments', n_reopened, n_closed; END IF;
    RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'rollback-ok';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'rollback-ok' THEN RAISE; END IF;
  END;

  -- F1: cost range present for every assessed demo building.
  IF EXISTS (SELECT 1 FROM v_building_status WHERE incident_id = inc AND (cost_low IS NULL OR cost_high < cost_low)) THEN
    RAISE EXCEPTION 'missing or invalid cost estimate';
  END IF;

  -- Citizen request auto-matched to the incident by location.
  IF EXISTS (SELECT 1 FROM citizen_requests WHERE incident_id IS NULL) THEN
    RAISE EXCEPTION 'citizen request was not matched to an incident';
  END IF;

  -- Live map cache follows the newest ping.
  IF (SELECT count(*) FROM responder_last_positions) <> 2 THEN
    RAISE EXCEPTION 'responder_last_positions not maintained';
  END IF;

  RAISE NOTICE 'Demo checks passed: % roads closed, % route invalidated, % responders warned',
               n_closed, n_invalid, n_notified;
END $$;

-- 7. pgRouting can route on the graph (detour around the closed street).
DO $$
DECLARE inc uuid; src bigint; dst bigint; hops int;
BEGIN
  SELECT id INTO inc FROM incidents WHERE code = 'INC-2026-0001';
  IF inc IS NULL THEN RETURN; END IF;
  SELECT r.source INTO src FROM road_segments r WHERE r.incident_id = inc AND r.name = 'El-Nile Street' ORDER BY ST_XMin(r.geom) LIMIT 1;
  SELECT r.target INTO dst FROM road_segments r WHERE r.incident_id = inc AND r.name = 'El-Nile Street' ORDER BY ST_XMax(r.geom) DESC LIMIT 1;
  SELECT count(*) INTO hops FROM pgr_dijkstra(
    format('SELECT id, source, target, cost, reverse_cost FROM road_segments WHERE incident_id = %L', inc),
    src, dst, directed => true);
  IF hops = 0 THEN RAISE EXCEPTION 'pgRouting found no detour'; END IF;
  IF EXISTS (SELECT 1 FROM pgr_dijkstra(
               format('SELECT id, source, target, cost, reverse_cost FROM road_segments WHERE incident_id = %L', inc),
               src, dst, directed => true) d
             JOIN road_segments s ON s.id = d.edge WHERE s.condition = 'HAZARD_CLOSED') THEN
    RAISE EXCEPTION 'detour uses a hazard-closed road';
  END IF;
  RAISE NOTICE 'pgRouting detour found: % steps, avoiding closed roads', hops;
END $$;
