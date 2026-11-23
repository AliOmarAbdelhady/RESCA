-- Security: database roles, session context, Row-Level Security, column
-- guards, audit trail.
--
-- Roles (cluster-wide, NOLOGIN groups; login roles are created per deployment
-- and granted membership, see database/README.md):
--   rv_app      the API acting for a signed-in agency user (RLS applies)
--   rv_worker   the AI / Celery pipeline (full data access, no user context)
--   rv_citizen  the public citizen channel (own requests only)
--   rv_readonly analytics and reporting (read-only, no personal data)
--
-- Per request the API runs, inside its transaction:
--   SELECT app.set_session_user('<user uuid>');      -- agency staff
--   SELECT app.set_session_citizen('<citizen uuid>');-- citizen app
-- Every policy derives agency, role and permissions from that id, so a
-- suspended user loses access on the next request.
--
-- The schema owner / migration role bypasses RLS (RLS is ENABLED, not FORCED)
-- and must never be used by an application.

CREATE SCHEMA IF NOT EXISTS app;

DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['rv_app', 'rv_worker', 'rv_citizen', 'rv_readonly'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE format('CREATE ROLE %I NOLOGIN', r);
    END IF;
  END LOOP;
END $$;

------------------------------------------------------------------------------
-- Session context helpers
------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.set_session_user(p_user uuid) RETURNS void
LANGUAGE sql VOLATILE AS $$
  SELECT set_config('app.user_id', p_user::text, true);   -- transaction-local
$$;

CREATE OR REPLACE FUNCTION app.set_session_citizen(p_citizen uuid) RETURNS void
LANGUAGE sql VOLATILE AS $$
  SELECT set_config('app.citizen_id', p_citizen::text, true);
$$;

CREATE OR REPLACE FUNCTION app.current_user_id() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.user_id', true), '')::uuid;
$$;

CREATE OR REPLACE FUNCTION app.current_citizen_id() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT nullif(current_setting('app.citizen_id', true), '')::uuid;
$$;

-- The helpers below read users / incident_agencies, which are themselves
-- protected by RLS, so they run as the owner (SECURITY DEFINER) with a fixed
-- search_path. Only ACTIVE, non-deleted users get an agency/role at all.
CREATE OR REPLACE FUNCTION app.current_agency_id() RETURNS uuid
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT agency_id FROM users
  WHERE id = app.current_user_id() AND status = 'ACTIVE' AND deleted_at IS NULL;
$$;

CREATE OR REPLACE FUNCTION app.current_role_code() RETURNS text
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT role_code FROM users
  WHERE id = app.current_user_id() AND status = 'ACTIVE' AND deleted_at IS NULL;
$$;

CREATE OR REPLACE FUNCTION app.is_platform_admin() RETURNS boolean
LANGUAGE sql STABLE AS $$
  SELECT coalesce(app.current_role_code() = 'PLATFORM_ADMIN', false);
$$;

CREATE OR REPLACE FUNCTION app.has_permission(p_permission text) RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT EXISTS (
    SELECT 1 FROM users u
    JOIN role_permissions rp ON rp.role_code = u.role_code
    WHERE u.id = app.current_user_id() AND u.status = 'ACTIVE' AND u.deleted_at IS NULL
      AND rp.permission_code = p_permission);
$$;

-- Incidents the current user may see: those their agency has ACTIVELY joined,
-- plus historical reference incidents. Platform Admin sees all.
CREATE OR REPLACE FUNCTION app.visible_incident_ids() RETURNS uuid[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT CASE
    WHEN app.is_platform_admin() THEN (SELECT coalesce(array_agg(id), '{}') FROM incidents)
    ELSE (SELECT coalesce(array_agg(DISTINCT x), '{}') FROM (
            SELECT ia.incident_id AS x FROM incident_agencies ia
            WHERE ia.agency_id = app.current_agency_id() AND ia.status = 'ACTIVE'
            UNION
            SELECT id FROM incidents WHERE is_historical) s)
  END;
$$;

-- Agencies the current user works alongside (own agency + co-participants in
-- any incident the agency has joined).
CREATE OR REPLACE FUNCTION app.partner_agency_ids() RETURNS uuid[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT coalesce(array_agg(DISTINCT ia2.agency_id), '{}') || coalesce(app.current_agency_id(), NULL)
  FROM incident_agencies ia1
  JOIN incident_agencies ia2 ON ia2.incident_id = ia1.incident_id AND ia2.status = 'ACTIVE'
  WHERE ia1.agency_id = app.current_agency_id() AND ia1.status = 'ACTIVE';
$$;

-- Incidents the agency is invited to / leads, and reports shared with it.
-- Used by policies that would otherwise reference each other's tables
-- (incidents <-> incident_agencies, reports <-> report_shares) and recurse.
CREATE OR REPLACE FUNCTION app.invited_incident_ids() RETURNS uuid[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT coalesce(array_agg(incident_id), '{}') FROM incident_agencies
  WHERE agency_id = app.current_agency_id() AND status = 'INVITED';
$$;

CREATE OR REPLACE FUNCTION app.led_incident_ids() RETURNS uuid[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT coalesce(array_agg(id), '{}') FROM incidents
  WHERE lead_agency_id = app.current_agency_id();
$$;

CREATE OR REPLACE FUNCTION app.shared_report_ids() RETURNS uuid[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT coalesce(array_agg(report_id), '{}') FROM report_shares
  WHERE agency_id = app.current_agency_id();
$$;

-- Missions the current user is assigned to, directly or through their team.
CREATE OR REPLACE FUNCTION app.my_mission_ids() RETURNS uuid[]
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT coalesce(array_agg(DISTINCT ma.mission_id), '{}')
  FROM mission_assignments ma
  LEFT JOIN team_members tm ON tm.team_id = ma.team_id AND tm.left_at IS NULL
  WHERE ma.released_at IS NULL
    AND (ma.user_id = app.current_user_id() OR tm.user_id = app.current_user_id());
$$;

-- Sign-in lookup: the only way the API role can read a password hash.
CREATE OR REPLACE FUNCTION app.get_login(p_email citext)
RETURNS TABLE (user_id uuid, password_hash text, status user_status)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp AS $$
  SELECT id, password_hash, status FROM users WHERE email = p_email AND deleted_at IS NULL;
$$;

-- An invited agency accepts or declines (the lead agency cannot do it for them).
CREATE OR REPLACE FUNCTION app.respond_to_invitation(p_incident uuid, p_accept boolean) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
BEGIN
  IF NOT app.has_permission('incident.invite') AND NOT app.has_permission('user.manage') THEN
    RAISE EXCEPTION USING ERRCODE = '42501', MESSAGE = 'Only a commander or agency admin can answer an invitation';
  END IF;
  UPDATE incident_agencies
     SET status = CASE WHEN p_accept THEN 'ACTIVE'::participation_status ELSE 'WITHDRAWN'::participation_status END,
         joined_at = CASE WHEN p_accept THEN now() END
   WHERE incident_id = p_incident AND agency_id = app.current_agency_id() AND status = 'INVITED';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'No open invitation for your agency on incident %', p_incident;
  END IF;
END $$;

------------------------------------------------------------------------------
-- Column guards: users without the named permission may change only the listed
-- columns (e.g. a responder may set a mission's status but not retarget it).
-- Usage: TRIGGER ... EXECUTE FUNCTION app.restrict_update('<permission>', 'col1', 'col2', ...)
------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.restrict_update() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  allowed text[] := TG_ARGV[1:];
BEGIN
  -- No user context = service / migration connection: not restricted here.
  IF app.current_user_id() IS NULL OR app.has_permission(TG_ARGV[0]) THEN
    RETURN NEW;
  END IF;
  IF (to_jsonb(NEW) - allowed) IS DISTINCT FROM (to_jsonb(OLD) - allowed) THEN
    RAISE EXCEPTION USING ERRCODE = '42501',
      MESSAGE = format('Without %s you may only change %s on %s',
                       TG_ARGV[0], array_to_string(allowed, ', '), TG_TABLE_NAME);
  END IF;
  RETURN NEW;
END $$;

-- "a_" prefix: fires before the updated_at triggers (alphabetical order).
CREATE TRIGGER a_guard_columns BEFORE UPDATE ON users FOR EACH ROW
  EXECUTE FUNCTION app.restrict_update('user.manage', 'full_name', 'phone', 'password_hash', 'last_login_at', 'updated_at');
CREATE TRIGGER a_guard_columns BEFORE UPDATE ON missions FOR EACH ROW
  EXECUTE FUNCTION app.restrict_update('mission.create', 'status', 'started_at', 'completed_at', 'updated_at');
CREATE TRIGGER a_guard_columns BEFORE UPDATE ON mission_assignments FOR EACH ROW
  EXECUTE FUNCTION app.restrict_update('mission.assign', 'response');
CREATE TRIGGER a_guard_columns BEFORE UPDATE ON assistance_cases FOR EACH ROW
  EXECUTE FUNCTION app.restrict_update('case.verify', 'status', 'triage', 'people_count', 'location',
                                       'location_error_m', 'transported_to_facility_id', 'closed_at', 'updated_at');

------------------------------------------------------------------------------
-- Audit trail (who changed what), written by the owner so no app role needs
-- INSERT on audit_log. Password hashes never enter the log.
------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION app.audit() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE
  b jsonb;
  a jsonb;
BEGIN
  IF TG_OP <> 'INSERT' THEN b := to_jsonb(OLD) - 'password_hash'; END IF;
  IF TG_OP <> 'DELETE' THEN a := to_jsonb(NEW) - 'password_hash'; END IF;
  INSERT INTO audit_log (actor_user_id, action, entity_table, entity_id, before, after, ip)
  VALUES (app.current_user_id(), TG_OP, TG_TABLE_NAME,
          coalesce(a ->> 'id', b ->> 'id',
                   concat_ws('/', coalesce(a, b) ->> 'incident_id', coalesce(a, b) ->> 'agency_id')),
          b, a, inet_client_addr());
  RETURN NULL;
END $$;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'agencies', 'users', 'role_permissions', 'teams', 'team_members', 'vehicles',
    'incidents', 'incident_agencies', 'zones', 'missions', 'mission_assignments',
    'ai_models', 'building_assessments', 'cost_profiles', 'cost_profile_unit_rates',
    'cost_profile_repair_ratios', 'assistance_cases', 'hazards', 'hazard_rules',
    'compound_alerts', 'infrastructure_assets', 'citizen_requests', 'sos_alerts',
    'reports', 'report_shares', 'facilities', 'routes']
  LOOP
    EXECUTE format('CREATE TRIGGER z_audit AFTER INSERT OR UPDATE OR DELETE ON %I
                    FOR EACH ROW EXECUTE FUNCTION app.audit()', t);
  END LOOP;
END $$;

------------------------------------------------------------------------------
-- Internal consistency triggers write to tables the caller may not write
-- directly (history, caches), so they run as the owner.
------------------------------------------------------------------------------
ALTER FUNCTION log_mission_status()              SECURITY DEFINER SET search_path = public, pg_temp;
ALTER FUNCTION log_case_changes()                SECURITY DEFINER SET search_path = public, pg_temp;
ALTER FUNCTION retire_previous_assessment()      SECURITY DEFINER SET search_path = public, pg_temp;
ALTER FUNCTION apply_road_observation()          SECURITY DEFINER SET search_path = public, pg_temp;
ALTER FUNCTION upsert_last_position()            SECURITY DEFINER SET search_path = public, pg_temp;
ALTER FUNCTION match_citizen_request_incident()  SECURITY DEFINER SET search_path = public, pg_temp;
-- The hazard engine stays SECURITY INVOKER on purpose: it runs with the
-- caller's rights, so only users allowed to write alerts/roads can fire it.

-- Views must respect the caller's RLS, not the view owner's.
ALTER VIEW v_building_status         SET (security_invoker = true);
ALTER VIEW v_incident_damage_summary SET (security_invoker = true);
ALTER VIEW v_open_cases              SET (security_invoker = true);
ALTER VIEW v_user_visible_incidents  SET (security_invoker = true);
ALTER VIEW v_routing_edges           SET (security_invoker = true);

------------------------------------------------------------------------------
-- Privileges
------------------------------------------------------------------------------
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA app FROM PUBLIC;
GRANT USAGE ON SCHEMA public, app TO rv_app, rv_worker, rv_citizen, rv_readonly;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO rv_app, rv_worker;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rv_readonly;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO rv_app, rv_worker, rv_citizen;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO rv_app, rv_worker, rv_citizen, rv_readonly;
GRANT EXECUTE ON FUNCTION evaluate_hazard_rules(uuid), resolve_compound_alert(uuid, uuid, text, boolean)
  TO rv_app, rv_worker;
REVOKE EXECUTE ON FUNCTION app.get_login(citext) FROM rv_citizen, rv_readonly, rv_worker;

-- Citizen channel: only its own tables.
GRANT SELECT, UPDATE ON citizens TO rv_citizen;
GRANT SELECT, INSERT ON citizen_requests, media_files, citizen_request_media TO rv_citizen;

-- Password hashes are not readable by any app role (sign-in uses app.get_login).
REVOKE SELECT ON users FROM rv_app, rv_worker, rv_readonly;
DO $$
DECLARE cols text;
BEGIN
  SELECT string_agg(quote_ident(attname), ', ' ORDER BY attnum) INTO cols
  FROM pg_attribute WHERE attrelid = 'users'::regclass AND attnum > 0 AND NOT attisdropped
    AND attname <> 'password_hash';
  EXECUTE format('GRANT SELECT (%s) ON users TO rv_app, rv_worker', cols);
END $$;

-- Analytics never sees credentials, sessions, citizens' identities or the audit trail.
REVOKE SELECT ON user_sessions, user_devices, citizens, audit_log FROM rv_readonly;

-- Partitions have no policies of their own: block direct access so nobody can
-- read responder_positions_2026_11 and skip RLS on the parent.
DO $$
DECLARE p regclass;
BEGIN
  FOR p IN SELECT c.oid::regclass FROM pg_class c
           WHERE c.relnamespace = 'public'::regnamespace AND c.relispartition AND c.relkind = 'r' LOOP
    EXECUTE format('REVOKE ALL ON %s FROM rv_app, rv_worker, rv_citizen, rv_readonly', p);
  END LOOP;
END $$;

------------------------------------------------------------------------------
-- Enable RLS everywhere (default deny), then the service / analytics policies
------------------------------------------------------------------------------
DO $$
DECLARE t text;
BEGIN
  FOR t IN SELECT c.relname FROM pg_class c
           WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p')
             AND NOT c.relispartition AND c.relname <> 'spatial_ref_sys' LOOP
    EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
    -- The AI pipeline acts on behalf of the platform, not a user.
    EXECUTE format('CREATE POLICY service_all ON %I FOR ALL TO rv_worker USING (true) WITH CHECK (true)', t);
    IF t NOT IN ('users', 'user_sessions', 'user_devices', 'citizens', 'audit_log') THEN
      EXECUTE format('CREATE POLICY analytics_read ON %I FOR SELECT TO rv_readonly USING (true)', t);
    END IF;
  END LOOP;
END $$;

------------------------------------------------------------------------------
-- rv_app policies (agency users). Shorthands used below:
--   visible  : incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
--   perm(x)  : (SELECT app.has_permission('x'))
--   me       : (SELECT app.current_user_id())
--   my agency: (SELECT app.current_agency_id())
-- Wrapping in (SELECT …) makes Postgres evaluate each once per statement.
-- Child tables without incident_id check their parent with EXISTS; the
-- parent's own RLS applies inside that subquery.
------------------------------------------------------------------------------

-- D1 Identity & Access ------------------------------------------------------
CREATE POLICY agencies_read ON agencies FOR SELECT TO rv_app
  USING ((SELECT app.current_user_id()) IS NOT NULL);
CREATE POLICY agencies_admin ON agencies FOR ALL TO rv_app
  USING ((SELECT app.has_permission('agency.manage')))
  WITH CHECK ((SELECT app.has_permission('agency.manage')));
CREATE POLICY agencies_own_update ON agencies FOR UPDATE TO rv_app
  USING (id = (SELECT app.current_agency_id()) AND (SELECT app.has_permission('user.manage')))
  WITH CHECK (id = (SELECT app.current_agency_id()));

CREATE POLICY roles_read ON roles FOR SELECT TO rv_app USING (true);
CREATE POLICY roles_admin ON roles FOR ALL TO rv_app
  USING ((SELECT app.has_permission('agency.manage'))) WITH CHECK ((SELECT app.has_permission('agency.manage')));
CREATE POLICY permissions_read ON permissions FOR SELECT TO rv_app USING (true);
CREATE POLICY permissions_admin ON permissions FOR ALL TO rv_app
  USING ((SELECT app.has_permission('agency.manage'))) WITH CHECK ((SELECT app.has_permission('agency.manage')));
CREATE POLICY role_permissions_read ON role_permissions FOR SELECT TO rv_app USING (true);
CREATE POLICY role_permissions_admin ON role_permissions FOR ALL TO rv_app
  USING ((SELECT app.has_permission('agency.manage'))) WITH CHECK ((SELECT app.has_permission('agency.manage')));

CREATE POLICY users_read ON users FOR SELECT TO rv_app
  USING (id = (SELECT app.current_user_id())
         OR agency_id = ANY ((SELECT app.partner_agency_ids())::uuid[])
         OR (SELECT app.is_platform_admin()));
CREATE POLICY users_self_update ON users FOR UPDATE TO rv_app
  USING (id = (SELECT app.current_user_id()))
  WITH CHECK (id = (SELECT app.current_user_id()));     -- column guard limits which fields
CREATE POLICY users_agency_admin ON users FOR ALL TO rv_app
  USING ((SELECT app.has_permission('user.manage'))
         AND ((SELECT app.is_platform_admin()) OR agency_id = (SELECT app.current_agency_id())))
  WITH CHECK ((SELECT app.has_permission('user.manage'))
              AND ((SELECT app.is_platform_admin())
                   OR (agency_id = (SELECT app.current_agency_id()) AND role_code <> 'PLATFORM_ADMIN')));

CREATE POLICY user_sessions_own ON user_sessions FOR ALL TO rv_app
  USING (user_id = (SELECT app.current_user_id())) WITH CHECK (user_id = (SELECT app.current_user_id()));
CREATE POLICY user_devices_own ON user_devices FOR ALL TO rv_app
  USING (user_id = (SELECT app.current_user_id())) WITH CHECK (user_id = (SELECT app.current_user_id()));

CREATE POLICY teams_read ON teams FOR SELECT TO rv_app
  USING (agency_id = ANY ((SELECT app.partner_agency_ids())::uuid[]) OR (SELECT app.is_platform_admin()));
CREATE POLICY teams_manage ON teams FOR ALL TO rv_app
  USING ((SELECT app.has_permission('team.manage')) AND agency_id = (SELECT app.current_agency_id()))
  WITH CHECK ((SELECT app.has_permission('team.manage')) AND agency_id = (SELECT app.current_agency_id()));
CREATE POLICY team_members_read ON team_members FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM teams t WHERE t.id = team_members.team_id));
CREATE POLICY team_members_manage ON team_members FOR ALL TO rv_app
  USING ((SELECT app.has_permission('team.manage'))
         AND EXISTS (SELECT 1 FROM teams t WHERE t.id = team_members.team_id AND t.agency_id = (SELECT app.current_agency_id())))
  WITH CHECK ((SELECT app.has_permission('team.manage'))
         AND EXISTS (SELECT 1 FROM teams t WHERE t.id = team_members.team_id AND t.agency_id = (SELECT app.current_agency_id())));
CREATE POLICY vehicles_read ON vehicles FOR SELECT TO rv_app
  USING (agency_id = ANY ((SELECT app.partner_agency_ids())::uuid[]) OR (SELECT app.is_platform_admin()));
CREATE POLICY vehicles_manage ON vehicles FOR ALL TO rv_app
  USING ((SELECT app.has_permission('team.manage')) AND agency_id = (SELECT app.current_agency_id()))
  WITH CHECK ((SELECT app.has_permission('team.manage')) AND agency_id = (SELECT app.current_agency_id()));

-- D2 Incidents & Operations --------------------------------------------------
CREATE POLICY incidents_read ON incidents FOR SELECT TO rv_app
  USING (id = ANY ((SELECT app.visible_incident_ids())::uuid[]) OR lead_agency_id = (SELECT app.current_agency_id())
         -- an invited agency can see the incident it is being asked to join
         OR id = ANY ((SELECT app.invited_incident_ids())::uuid[]));
CREATE POLICY incidents_create ON incidents FOR INSERT TO rv_app
  WITH CHECK ((SELECT app.has_permission('incident.create'))
              AND ((SELECT app.is_platform_admin()) OR lead_agency_id = (SELECT app.current_agency_id())));
CREATE POLICY incidents_lead_update ON incidents FOR UPDATE TO rv_app
  USING ((SELECT app.has_permission('incident.create'))
         AND ((SELECT app.is_platform_admin()) OR lead_agency_id = (SELECT app.current_agency_id())))
  WITH CHECK ((SELECT app.is_platform_admin()) OR lead_agency_id = (SELECT app.current_agency_id()));
CREATE POLICY incidents_admin_delete ON incidents FOR DELETE TO rv_app USING ((SELECT app.is_platform_admin()));

CREATE POLICY incident_agencies_read ON incident_agencies FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) OR agency_id = (SELECT app.current_agency_id()));
-- Only the lead agency's commanders invite or change participation; invited
-- agencies answer through app.respond_to_invitation().
CREATE POLICY incident_agencies_lead_manage ON incident_agencies FOR ALL TO rv_app
  USING ((SELECT app.has_permission('incident.invite'))
         AND ((SELECT app.is_platform_admin())
              OR incident_id = ANY ((SELECT app.led_incident_ids())::uuid[])))
  WITH CHECK ((SELECT app.has_permission('incident.invite'))
         AND ((SELECT app.is_platform_admin())
              OR incident_id = ANY ((SELECT app.led_incident_ids())::uuid[])));

CREATE POLICY zones_read ON zones FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY zones_write ON zones FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('mission.create')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('mission.create')));

CREATE POLICY missions_read ON missions FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
-- Commanders manage their own agency's missions inside joined incidents.
CREATE POLICY missions_manage ON missions FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('mission.create'))
         AND ((SELECT app.is_platform_admin()) OR agency_id = (SELECT app.current_agency_id())))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('mission.create'))
         AND ((SELECT app.is_platform_admin()) OR agency_id = (SELECT app.current_agency_id())));
-- Assigned responders update progress (column guard: status fields only).
CREATE POLICY missions_assignee_update ON missions FOR UPDATE TO rv_app
  USING (id = ANY ((SELECT app.my_mission_ids())::uuid[]) AND (SELECT app.has_permission('mission.update_status')))
  WITH CHECK (id = ANY ((SELECT app.my_mission_ids())::uuid[]));

CREATE POLICY mission_assignments_read ON mission_assignments FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM missions m WHERE m.id = mission_assignments.mission_id));
CREATE POLICY mission_assignments_manage ON mission_assignments FOR ALL TO rv_app
  USING ((SELECT app.has_permission('mission.assign'))
         AND EXISTS (SELECT 1 FROM missions m WHERE m.id = mission_assignments.mission_id
                     AND ((SELECT app.is_platform_admin()) OR m.agency_id = (SELECT app.current_agency_id()))))
  WITH CHECK ((SELECT app.has_permission('mission.assign'))
         AND EXISTS (SELECT 1 FROM missions m WHERE m.id = mission_assignments.mission_id
                     AND ((SELECT app.is_platform_admin()) OR m.agency_id = (SELECT app.current_agency_id()))));
-- The assignee accepts or declines (column guard: response only).
CREATE POLICY mission_assignments_respond ON mission_assignments FOR UPDATE TO rv_app
  USING (mission_id = ANY ((SELECT app.my_mission_ids())::uuid[]))
  WITH CHECK (mission_id = ANY ((SELECT app.my_mission_ids())::uuid[]));

CREATE POLICY mission_status_history_read ON mission_status_history FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM missions m WHERE m.id = mission_status_history.mission_id));

-- D3 Imagery & AI ------------------------------------------------------------
CREATE POLICY capture_sessions_read ON capture_sessions FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY capture_sessions_upload ON capture_sessions FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('imagery.upload')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('imagery.upload')));

CREATE POLICY images_read ON images FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM capture_sessions s WHERE s.id = images.session_id));
CREATE POLICY images_upload ON images FOR INSERT TO rv_app
  WITH CHECK ((SELECT app.has_permission('imagery.upload'))
              AND EXISTS (SELECT 1 FROM capture_sessions s WHERE s.id = images.session_id));
CREATE POLICY raster_products_read ON raster_products FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM capture_sessions s WHERE s.id = raster_products.session_id));

CREATE POLICY ai_models_read ON ai_models FOR SELECT TO rv_app USING (true);
CREATE POLICY ai_models_admin ON ai_models FOR ALL TO rv_app
  USING ((SELECT app.has_permission('model.manage'))) WITH CHECK ((SELECT app.has_permission('model.manage')));

CREATE POLICY processing_jobs_read ON processing_jobs FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY processing_jobs_request ON processing_jobs FOR INSERT TO rv_app
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('analysis.run'))
              AND requested_by = (SELECT app.current_user_id()));
CREATE POLICY inference_runs_read ON inference_runs FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM processing_jobs j WHERE j.id = inference_runs.job_id));

-- F1 Buildings & Cost -------------------------------------------------------
CREATE POLICY buildings_read ON buildings FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY buildings_write ON buildings FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('analysis.run')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('analysis.run')));

CREATE POLICY building_assessments_read ON building_assessments FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM buildings b WHERE b.id = building_assessments.building_id));
CREATE POLICY building_assessments_review ON building_assessments FOR ALL TO rv_app
  USING ((SELECT app.has_permission('assessment.review'))
         AND EXISTS (SELECT 1 FROM buildings b WHERE b.id = building_assessments.building_id))
  WITH CHECK ((SELECT app.has_permission('assessment.review'))
         AND EXISTS (SELECT 1 FROM buildings b WHERE b.id = building_assessments.building_id));

CREATE POLICY cost_profiles_read ON cost_profiles FOR SELECT TO rv_app USING (true);
CREATE POLICY cost_profiles_edit ON cost_profiles FOR ALL TO rv_app
  USING ((SELECT app.has_permission('cost.edit_profile'))) WITH CHECK ((SELECT app.has_permission('cost.edit_profile')));
CREATE POLICY cost_profile_unit_rates_read ON cost_profile_unit_rates FOR SELECT TO rv_app USING (true);
CREATE POLICY cost_profile_unit_rates_edit ON cost_profile_unit_rates FOR ALL TO rv_app
  USING ((SELECT app.has_permission('cost.edit_profile'))) WITH CHECK ((SELECT app.has_permission('cost.edit_profile')));
CREATE POLICY cost_profile_repair_ratios_read ON cost_profile_repair_ratios FOR SELECT TO rv_app USING (true);
CREATE POLICY cost_profile_repair_ratios_edit ON cost_profile_repair_ratios FOR ALL TO rv_app
  USING ((SELECT app.has_permission('cost.edit_profile'))) WITH CHECK ((SELECT app.has_permission('cost.edit_profile')));

CREATE POLICY cost_estimates_read ON cost_estimates FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM buildings b WHERE b.id = cost_estimates.building_id));
CREATE POLICY cost_estimates_write ON cost_estimates FOR INSERT TO rv_app
  WITH CHECK ((SELECT app.has_permission('assessment.review'))
              AND EXISTS (SELECT 1 FROM buildings b WHERE b.id = cost_estimates.building_id));

-- F2 Roads & Routing ----------------------------------------------------------
CREATE POLICY road_nodes_read ON road_nodes FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY road_nodes_write ON road_nodes FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('analysis.run')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('analysis.run')));

CREATE POLICY road_segments_read ON road_segments FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
-- Analysts load the network; the hazard engine (run by analysts or alert
-- resolvers) opens and closes roads.
CREATE POLICY road_segments_write ON road_segments FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))));

CREATE POLICY road_condition_observations_read ON road_condition_observations FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM road_segments s WHERE s.id = road_condition_observations.segment_id));
CREATE POLICY road_condition_observations_report ON road_condition_observations FOR INSERT TO rv_app
  WITH CHECK ((SELECT app.has_permission('hazard.report'))
              AND reported_by = (SELECT app.current_user_id())
              AND EXISTS (SELECT 1 FROM road_segments s WHERE s.id = road_condition_observations.segment_id));

CREATE POLICY routes_read ON routes FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY routes_plan ON routes FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('route.plan')) OR (SELECT app.has_permission('alert.resolve'))))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('route.plan')) OR (SELECT app.has_permission('alert.resolve'))));
CREATE POLICY route_segments_read ON route_segments FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM routes r WHERE r.id = route_segments.route_id));
CREATE POLICY route_segments_plan ON route_segments FOR ALL TO rv_app
  USING ((SELECT app.has_permission('route.plan')) AND EXISTS (SELECT 1 FROM routes r WHERE r.id = route_segments.route_id))
  WITH CHECK ((SELECT app.has_permission('route.plan')) AND EXISTS (SELECT 1 FROM routes r WHERE r.id = route_segments.route_id));

-- F3/F4 Persons & Cases -------------------------------------------------------
CREATE POLICY person_tracks_read ON person_tracks FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY person_detections_read ON person_detections FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));

CREATE POLICY facilities_read ON facilities FOR SELECT TO rv_app
  USING ((SELECT app.current_user_id()) IS NOT NULL);
CREATE POLICY facilities_manage ON facilities FOR ALL TO rv_app
  USING ((SELECT app.has_permission('team.manage'))
         AND ((SELECT app.is_platform_admin()) OR agency_id = (SELECT app.current_agency_id())))
  WITH CHECK ((SELECT app.has_permission('team.manage'))
         AND ((SELECT app.is_platform_admin()) OR agency_id = (SELECT app.current_agency_id())));

CREATE POLICY assistance_cases_read ON assistance_cases FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY assistance_cases_verify ON assistance_cases FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('case.verify')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('case.verify')));
-- A responder can open a case they found in the field …
CREATE POLICY assistance_cases_field_report ON assistance_cases FOR INSERT TO rv_app
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('hazard.report'))
              AND source = 'RESPONDER_REPORT' AND reported_by = (SELECT app.current_user_id()));
-- … and update cases on missions they are assigned to (column guard applies).
CREATE POLICY assistance_cases_field_update ON assistance_cases FOR UPDATE TO rv_app
  USING (assigned_mission_id = ANY ((SELECT app.my_mission_ids())::uuid[]) AND (SELECT app.has_permission('case.update')))
  WITH CHECK (assigned_mission_id = ANY ((SELECT app.my_mission_ids())::uuid[]));

CREATE POLICY case_events_read ON case_events FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM assistance_cases c WHERE c.id = case_events.case_id));
CREATE POLICY case_events_add ON case_events FOR INSERT TO rv_app
  WITH CHECK (actor_id = (SELECT app.current_user_id())
              AND EXISTS (SELECT 1 FROM assistance_cases c WHERE c.id = case_events.case_id));

-- F5 Hazards & Alerts ---------------------------------------------------------
CREATE POLICY infrastructure_assets_read ON infrastructure_assets FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY infrastructure_assets_write ON infrastructure_assets FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))));

CREATE POLICY hazards_read ON hazards FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY hazards_report ON hazards FOR INSERT TO rv_app
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('hazard.report'))
              AND origin = 'RESPONDER_REPORTED' AND reported_by = (SELECT app.current_user_id()));
CREATE POLICY hazards_manage ON hazards FOR UPDATE TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('alert.resolve')) OR (SELECT app.has_permission('case.verify'))))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));

CREATE POLICY hazard_rules_read ON hazard_rules FOR SELECT TO rv_app USING (true);
CREATE POLICY hazard_rules_admin ON hazard_rules FOR ALL TO rv_app
  USING ((SELECT app.has_permission('rule.manage'))) WITH CHECK ((SELECT app.has_permission('rule.manage')));

CREATE POLICY compound_alerts_read ON compound_alerts FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY compound_alerts_engine ON compound_alerts FOR ALL TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
         AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))));
CREATE POLICY compound_alert_sources_read ON compound_alert_sources FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM compound_alerts a WHERE a.id = compound_alert_sources.alert_id));
CREATE POLICY compound_alert_sources_engine ON compound_alert_sources FOR INSERT TO rv_app
  WITH CHECK (EXISTS (SELECT 1 FROM compound_alerts a WHERE a.id = compound_alert_sources.alert_id)
              AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))));
CREATE POLICY alert_closed_segments_read ON alert_closed_segments FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM compound_alerts a WHERE a.id = alert_closed_segments.alert_id));
CREATE POLICY alert_closed_segments_engine ON alert_closed_segments FOR INSERT TO rv_app
  WITH CHECK (EXISTS (SELECT 1 FROM compound_alerts a WHERE a.id = alert_closed_segments.alert_id)
              AND ((SELECT app.has_permission('analysis.run')) OR (SELECT app.has_permission('alert.resolve'))));

-- Citizens & media (staff side) ----------------------------------------------
CREATE POLICY citizens_staff_read ON citizens FOR SELECT TO rv_app
  USING ((SELECT app.has_permission('case.verify'))
         AND EXISTS (SELECT 1 FROM citizen_requests r WHERE r.citizen_id = citizens.id));
CREATE POLICY citizens_admin_block ON citizens FOR UPDATE TO rv_app
  USING ((SELECT app.is_platform_admin())) WITH CHECK ((SELECT app.is_platform_admin()));

CREATE POLICY citizen_requests_staff_read ON citizen_requests FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('case.verify')));
CREATE POLICY citizen_requests_staff_verify ON citizen_requests FOR UPDATE TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('case.verify')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY citizen_request_media_staff_read ON citizen_request_media FOR SELECT TO rv_app
  USING (EXISTS (SELECT 1 FROM citizen_requests r WHERE r.id = citizen_request_media.request_id));

CREATE POLICY media_files_read ON media_files FOR SELECT TO rv_app
  USING (uploaded_by_user = (SELECT app.current_user_id())
         OR EXISTS (SELECT 1 FROM citizen_request_media m WHERE m.media_id = media_files.id)
         OR EXISTS (SELECT 1 FROM case_events e WHERE e.media_id = media_files.id)
         OR EXISTS (SELECT 1 FROM sos_alerts s WHERE s.media_id = media_files.id));
CREATE POLICY media_files_upload ON media_files FOR INSERT TO rv_app
  WITH CHECK (uploaded_by_user = (SELECT app.current_user_id()) AND uploaded_by_citizen IS NULL);

-- Field channel -----------------------------------------------------------------
CREATE POLICY responder_positions_read ON responder_positions FOR SELECT TO rv_app
  USING (user_id = (SELECT app.current_user_id()) OR incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY responder_positions_share ON responder_positions FOR INSERT TO rv_app
  WITH CHECK (user_id = (SELECT app.current_user_id()) AND (SELECT app.has_permission('position.share')));
CREATE POLICY responder_last_positions_read ON responder_last_positions FOR SELECT TO rv_app
  USING (user_id = (SELECT app.current_user_id()) OR incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));

CREATE POLICY sos_alerts_read ON sos_alerts FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY sos_alerts_raise ON sos_alerts FOR INSERT TO rv_app
  WITH CHECK (user_id = (SELECT app.current_user_id()) AND (SELECT app.has_permission('sos.raise'))
              AND incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));
CREATE POLICY sos_alerts_respond ON sos_alerts FOR UPDATE TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('sos.respond')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));

CREATE POLICY notifications_own ON notifications FOR SELECT TO rv_app
  USING (user_id = (SELECT app.current_user_id()));
CREATE POLICY notifications_mark_read ON notifications FOR UPDATE TO rv_app
  USING (user_id = (SELECT app.current_user_id())) WITH CHECK (user_id = (SELECT app.current_user_id()));
-- Command staff and the hazard engine may notify people working the incident.
CREATE POLICY notifications_send ON notifications FOR INSERT TO rv_app
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
              AND ((SELECT app.has_permission('mission.assign')) OR (SELECT app.has_permission('analysis.run'))
                   OR (SELECT app.has_permission('alert.resolve'))));

-- Reports: drafts stay inside the authoring agency until approved; shared
-- reports are visible to the agencies they were shared with.
CREATE POLICY reports_read ON reports FOR SELECT TO rv_app
  USING ((incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[])
          AND (status IN ('APPROVED', 'PUBLISHED')
               OR EXISTS (SELECT 1 FROM users u WHERE u.id = reports.generated_by
                          AND u.agency_id = (SELECT app.current_agency_id()))))
         OR id = ANY ((SELECT app.shared_report_ids())::uuid[])
         OR (SELECT app.is_platform_admin()));
CREATE POLICY reports_generate ON reports FOR INSERT TO rv_app
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('report.generate'))
              AND generated_by = (SELECT app.current_user_id()));
CREATE POLICY reports_approve ON reports FOR UPDATE TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]) AND (SELECT app.has_permission('report.approve')))
  WITH CHECK (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));

CREATE POLICY report_shares_read ON report_shares FOR SELECT TO rv_app
  USING (agency_id = (SELECT app.current_agency_id()) OR EXISTS (SELECT 1 FROM reports r WHERE r.id = report_shares.report_id));
CREATE POLICY report_shares_share ON report_shares FOR INSERT TO rv_app
  WITH CHECK ((SELECT app.has_permission('report.share'))
              AND EXISTS (SELECT 1 FROM reports r WHERE r.id = report_shares.report_id));

CREATE POLICY image_embeddings_read ON image_embeddings FOR SELECT TO rv_app
  USING (incident_id = ANY ((SELECT app.visible_incident_ids())::uuid[]));

CREATE POLICY audit_log_admin_read ON audit_log FOR SELECT TO rv_app
  USING ((SELECT app.is_platform_admin()));

------------------------------------------------------------------------------
-- rv_citizen policies (public citizen channel)
------------------------------------------------------------------------------
CREATE POLICY citizens_self ON citizens FOR SELECT TO rv_citizen
  USING (id = (SELECT app.current_citizen_id()));
CREATE POLICY citizens_self_update ON citizens FOR UPDATE TO rv_citizen
  USING (id = (SELECT app.current_citizen_id())) WITH CHECK (id = (SELECT app.current_citizen_id()) AND NOT is_blocked);
CREATE POLICY citizen_requests_own ON citizen_requests FOR SELECT TO rv_citizen
  USING (citizen_id = (SELECT app.current_citizen_id()));
CREATE POLICY citizen_requests_submit ON citizen_requests FOR INSERT TO rv_citizen
  WITH CHECK (citizen_id = (SELECT app.current_citizen_id()) AND status = 'RECEIVED'
              AND NOT EXISTS (SELECT 1 FROM citizens c WHERE c.id = (SELECT app.current_citizen_id()) AND c.is_blocked));
CREATE POLICY media_files_citizen ON media_files FOR ALL TO rv_citizen
  USING (uploaded_by_citizen = (SELECT app.current_citizen_id()))
  WITH CHECK (uploaded_by_citizen = (SELECT app.current_citizen_id()) AND uploaded_by_user IS NULL);
CREATE POLICY citizen_request_media_citizen ON citizen_request_media FOR ALL TO rv_citizen
  USING (EXISTS (SELECT 1 FROM citizen_requests r WHERE r.id = citizen_request_media.request_id))
  WITH CHECK (EXISTS (SELECT 1 FROM citizen_requests r WHERE r.id = citizen_request_media.request_id));
