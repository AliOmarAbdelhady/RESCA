-- Read models for the dashboard and reports (views, no new tables)

-- F1: current damage + latest cost per building
CREATE OR REPLACE VIEW v_building_status AS
SELECT b.id AS building_id, b.incident_id, b.footprint, b.area_m2, b.floors, b.occupancy,
       a.damage_grade, a.p_destroyed, a.review_status, a.method,
       ce.cost_low, ce.cost_high, ce.currency
FROM buildings b
LEFT JOIN building_assessments a ON a.building_id = b.id AND a.is_current
LEFT JOIN LATERAL (
  SELECT cost_low, cost_high, currency FROM cost_estimates
  WHERE building_id = b.id ORDER BY computed_at DESC LIMIT 1
) ce ON true;

-- F1/F6: damage and cost totals per incident
CREATE OR REPLACE VIEW v_incident_damage_summary AS
SELECT incident_id,
       count(*)                                               AS buildings,
       count(*) FILTER (WHERE damage_grade = 'NO_DAMAGE')     AS no_damage,
       count(*) FILTER (WHERE damage_grade = 'MINOR')         AS minor,
       count(*) FILTER (WHERE damage_grade = 'MAJOR')         AS major,
       count(*) FILTER (WHERE damage_grade = 'DESTROYED')     AS destroyed,
       count(*) FILTER (WHERE damage_grade IS NULL)           AS not_assessed,
       sum(cost_low)  AS total_cost_low,
       sum(cost_high) AS total_cost_high
FROM v_building_status
GROUP BY incident_id;

-- F4/F6: open assistance cases with triage colour and hazard proximity
CREATE OR REPLACE VIEW v_open_cases AS
SELECT c.id, c.incident_id, c.code, c.source, c.status, c.triage,
       CASE c.triage WHEN 'IMMEDIATE' THEN 'red' WHEN 'DELAYED' THEN 'yellow'
                     WHEN 'MINOR' THEN 'green' WHEN 'EXPECTANT' THEN 'black' ELSE 'grey' END AS triage_colour,
       c.people_count, c.location, c.location_error_m, c.priority_score, c.assigned_mission_id,
       EXISTS (SELECT 1 FROM compound_alerts a
               WHERE a.incident_id = c.incident_id AND a.status IN ('ACTIVE', 'ACKNOWLEDGED')
                 AND ST_Intersects(a.danger_zone, c.location)) AS inside_danger_zone
FROM assistance_cases c
WHERE c.closed_at IS NULL;

-- Access control: incidents a user may see (their agency joined it, or Platform Admin)
CREATE OR REPLACE VIEW v_user_visible_incidents AS
SELECT u.id AS user_id, i.id AS incident_id
FROM users u
JOIN incidents i ON u.role_code = 'PLATFORM_ADMIN'
              OR EXISTS (SELECT 1 FROM incident_agencies ia
                         WHERE ia.incident_id = i.id AND ia.agency_id = u.agency_id AND ia.status = 'ACTIVE')
WHERE u.deleted_at IS NULL AND u.status = 'ACTIVE';

-- F2: routable edges for pgRouting (closed segments already carry negative cost)
CREATE OR REPLACE VIEW v_routing_edges AS
SELECT id, source, target, cost, reverse_cost, incident_id,
       ST_X(ST_StartPoint(geom)) AS x1, ST_Y(ST_StartPoint(geom)) AS y1,
       ST_X(ST_EndPoint(geom))   AS x2, ST_Y(ST_EndPoint(geom))   AS y2
FROM road_segments;
