-- F5 · Compound hazard rule engine (functions, no new tables)
--
-- evaluate_hazard_rules(incident)  : fire every active rule, open alerts,
--                                    close roads, invalidate routes, notify.
-- resolve_compound_alert(alert, …) : close the alert and re-open its roads.

-- Fire all active hazard rules for one incident. Returns the new alert ids.
-- Idempotent: a hazard/asset pair already covered by a live alert of the same
-- rule does not open a second alert.
CREATE OR REPLACE FUNCTION evaluate_hazard_rules(p_incident uuid)
RETURNS SETOF uuid LANGUAGE plpgsql AS $$
DECLARE
  r        hazard_rules%ROWTYPE;
  h        hazards%ROWTYPE;
  v_zone   geometry;
  v_alert  uuid;
  v_street text;
BEGIN
  FOR r IN SELECT * FROM hazard_rules WHERE is_active LOOP
    FOR h IN
      SELECT * FROM hazards
      WHERE incident_id = p_incident
        AND hazard_type = r.primary_hazard_type
        AND status IN ('SUSPECTED', 'CONFIRMED')
        AND (expires_at IS NULL OR expires_at > now())
    LOOP
      -- Skip if this hazard already feeds a live alert of this rule.
      CONTINUE WHEN EXISTS (
        SELECT 1 FROM compound_alert_sources s
        JOIN compound_alerts a ON a.id = s.alert_id
        WHERE s.hazard_id = h.id AND a.rule_id = r.id AND a.status IN ('ACTIVE', 'ACKNOWLEDGED'));

      v_alert := NULL;

      IF r.secondary_kind = 'ASSET' THEN
        -- e.g. FLOOD_WATER near an energized POWER_LINE / TRANSFORMER
        WITH partners AS (
          SELECT a.id, a.geom FROM infrastructure_assets a
          WHERE a.incident_id = p_incident
            AND a.asset_type::text = ANY (r.secondary_types)
            AND a.power_state <> 'DE_ENERGIZED'
            AND ST_DWithin(h.geom::geography, a.geom::geography, r.max_distance_m))
        SELECT ST_Multi(ST_Buffer(ST_Union(h.geom, ST_Union(p.geom))::geography, r.danger_buffer_m)::geometry)
          INTO v_zone FROM partners p HAVING count(*) > 0;

        IF v_zone IS NOT NULL THEN
          INSERT INTO compound_alerts (incident_id, rule_id, title, danger_zone, severity)
          VALUES (p_incident, r.id, r.name, v_zone, r.resulting_severity)
          RETURNING id INTO v_alert;
          INSERT INTO compound_alert_sources (alert_id, hazard_id) VALUES (v_alert, h.id);
          INSERT INTO compound_alert_sources (alert_id, asset_id)
          SELECT v_alert, a.id FROM infrastructure_assets a
          WHERE a.incident_id = p_incident
            AND a.asset_type::text = ANY (r.secondary_types)
            AND a.power_state <> 'DE_ENERGIZED'
            AND ST_DWithin(h.geom::geography, a.geom::geography, r.max_distance_m);
        END IF;

      ELSIF r.secondary_kind = 'HAZARD' THEN
        -- e.g. FIRE near a GAS_LEAK, FLOOD_WATER near a DOWNED_POWER_LINE
        WITH partners AS (
          SELECT o.id, o.geom FROM hazards o
          WHERE o.incident_id = p_incident AND o.id <> h.id
            AND o.hazard_type::text = ANY (r.secondary_types)
            AND o.status IN ('SUSPECTED', 'CONFIRMED')
            AND ST_DWithin(h.geom::geography, o.geom::geography, r.max_distance_m))
        SELECT ST_Multi(ST_Buffer(ST_Union(h.geom, ST_Union(p.geom))::geography, r.danger_buffer_m)::geometry)
          INTO v_zone FROM partners p HAVING count(*) > 0;

        IF v_zone IS NOT NULL THEN
          INSERT INTO compound_alerts (incident_id, rule_id, title, danger_zone, severity)
          VALUES (p_incident, r.id, r.name, v_zone, r.resulting_severity)
          RETURNING id INTO v_alert;
          INSERT INTO compound_alert_sources (alert_id, hazard_id) VALUES (v_alert, h.id);
          INSERT INTO compound_alert_sources (alert_id, hazard_id)
          SELECT v_alert, o.id FROM hazards o
          WHERE o.incident_id = p_incident AND o.id <> h.id
            AND o.hazard_type::text = ANY (r.secondary_types)
            AND o.status IN ('SUSPECTED', 'CONFIRMED')
            AND ST_DWithin(h.geom::geography, o.geom::geography, r.max_distance_m);
        END IF;

      ELSIF r.secondary_kind = 'ROAD' THEN
        -- e.g. COLLAPSE_RISK building next to a road → falling-debris zone
        IF EXISTS (SELECT 1 FROM road_segments s
                   WHERE s.incident_id = p_incident
                     AND ST_DWithin(h.geom::geography, s.geom::geography, r.max_distance_m)) THEN
          v_zone := ST_Multi(ST_Buffer(h.geom::geography, r.danger_buffer_m)::geometry);
          INSERT INTO compound_alerts (incident_id, rule_id, title, danger_zone, severity)
          VALUES (p_incident, r.id, r.name, v_zone, r.resulting_severity)
          RETURNING id INTO v_alert;
          INSERT INTO compound_alert_sources (alert_id, hazard_id) VALUES (v_alert, h.id);
        END IF;
      END IF;

      CONTINUE WHEN v_alert IS NULL;

      -- Name the street in the title/warning when one is inside the zone.
      SELECT s.name INTO v_street FROM road_segments s
      WHERE s.incident_id = p_incident AND s.name IS NOT NULL AND ST_Intersects(s.geom, v_zone)
      LIMIT 1;
      UPDATE compound_alerts
         SET title = r.name || COALESCE(' – ' || v_street, '')
       WHERE id = v_alert;

      IF r.closes_roads THEN
        -- 1. close every road segment that crosses the danger zone
        INSERT INTO alert_closed_segments (alert_id, segment_id, prev_condition, prev_cost, prev_reverse_cost)
        SELECT v_alert, s.id, s.condition, s.cost, s.reverse_cost
        FROM road_segments s
        WHERE s.incident_id = p_incident AND ST_Intersects(s.geom, v_zone)
        ON CONFLICT DO NOTHING;

        UPDATE road_segments s
           SET condition = 'HAZARD_CLOSED', cost = -1, reverse_cost = -1, condition_updated_at = now()
          FROM alert_closed_segments c
         WHERE c.alert_id = v_alert AND c.segment_id = s.id;

        -- 2. invalidate active routes that use any closed segment
        UPDATE routes rt
           SET status = 'INVALIDATED', invalidated_by_alert_id = v_alert
         WHERE rt.status = 'ACTIVE'
           AND rt.incident_id = p_incident
           AND EXISTS (SELECT 1 FROM route_segments rs
                       JOIN alert_closed_segments c ON c.segment_id = rs.segment_id AND c.alert_id = v_alert
                       WHERE rs.route_id = rt.id);
      END IF;

      -- 3. warn responders inside the zone and teams whose route was cut
      INSERT INTO notifications (user_id, incident_id, kind, title, body, severity, alert_id)
      SELECT DISTINCT u.user_id, p_incident, 'HAZARD_ALERT'::notification_kind,
             r.name, replace(r.warning_template, '{street}', COALESCE(v_street, 'this area')),
             r.resulting_severity, v_alert
      FROM (
        SELECT lp.user_id FROM responder_last_positions lp
        WHERE ST_DWithin(lp.geom::geography, v_zone::geography, 0)
        UNION
        SELECT COALESCE(ma.user_id, tm.user_id)
        FROM routes rt
        JOIN mission_assignments ma ON ma.mission_id = rt.mission_id AND ma.released_at IS NULL
        LEFT JOIN team_members tm   ON tm.team_id = ma.team_id AND tm.left_at IS NULL
        WHERE rt.invalidated_by_alert_id = v_alert
      ) u
      WHERE u.user_id IS NOT NULL;

      RETURN NEXT v_alert;
    END LOOP;
  END LOOP;
END $$;

-- Resolve (or dismiss) an alert and re-open the roads it closed, unless another
-- live alert still covers the same segment.
CREATE OR REPLACE FUNCTION resolve_compound_alert(
  p_alert uuid, p_user uuid, p_note text DEFAULT NULL, p_false_alarm boolean DEFAULT false)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE
  v_reopened integer;
BEGIN
  UPDATE compound_alerts
     SET status = CASE WHEN p_false_alarm THEN 'FALSE_ALARM'::alert_status ELSE 'RESOLVED'::alert_status END,
         resolved_by = p_user, resolved_at = now(), resolution_note = p_note
   WHERE id = p_alert AND status IN ('ACTIVE', 'ACKNOWLEDGED');
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Alert % is not active', p_alert;
  END IF;

  UPDATE road_segments s
     SET condition = c.prev_condition, cost = c.prev_cost, reverse_cost = c.prev_reverse_cost,
         condition_updated_at = now()
    FROM alert_closed_segments c
   WHERE c.alert_id = p_alert AND c.segment_id = s.id
     AND NOT EXISTS (SELECT 1 FROM alert_closed_segments c2
                     JOIN compound_alerts a2 ON a2.id = c2.alert_id
                     WHERE c2.segment_id = s.id AND c2.alert_id <> p_alert
                       AND a2.status IN ('ACTIVE', 'ACKNOWLEDGED'));
  GET DIAGNOSTICS v_reopened = ROW_COUNT;
  RETURN v_reopened;
END $$;
