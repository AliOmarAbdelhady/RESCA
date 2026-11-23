-- Supporting indexes for foreign keys that are joined on or cascade on delete.
-- (Audit-style "who did it" user columns are left unindexed on purpose: users
--  are soft-deleted and those columns are rarely used as join keys.)

CREATE INDEX incidents_lead_agency_idx             ON incidents (lead_agency_id);
CREATE INDEX missions_target_zone_idx              ON missions (target_zone_id);
CREATE INDEX mission_assignments_vehicle_idx       ON mission_assignments (vehicle_id);
CREATE INDEX capture_sessions_mission_idx          ON capture_sessions (mission_id);
CREATE INDEX processing_jobs_session_idx           ON processing_jobs (session_id);
CREATE INDEX inference_runs_pre_raster_idx         ON inference_runs (pre_raster_id);
CREATE INDEX inference_runs_post_raster_idx        ON inference_runs (post_raster_id);
CREATE INDEX media_files_user_idx                  ON media_files (uploaded_by_user);
CREATE INDEX media_files_citizen_idx               ON media_files (uploaded_by_citizen);
CREATE INDEX citizen_requests_duplicate_idx        ON citizen_requests (duplicate_of_id);
CREATE INDEX building_assessments_pre_image_idx    ON building_assessments (pre_image_id);
CREATE INDEX building_assessments_post_image_idx   ON building_assessments (post_image_id);
CREATE INDEX road_condition_observations_run_idx   ON road_condition_observations (inference_run_id);
CREATE INDEX road_condition_observations_req_idx   ON road_condition_observations (citizen_request_id);
CREATE INDEX person_detections_incident_idx        ON person_detections (incident_id);
CREATE INDEX facilities_agency_idx                 ON facilities (agency_id);
CREATE INDEX assistance_cases_building_idx         ON assistance_cases (building_id);
CREATE INDEX assistance_cases_facility_idx         ON assistance_cases (transported_to_facility_id);
CREATE INDEX case_events_media_idx                 ON case_events (media_id);
CREATE INDEX hazards_run_idx                       ON hazards (inference_run_id);
CREATE INDEX hazards_citizen_request_idx           ON hazards (citizen_request_id);
CREATE INDEX compound_alerts_rule_idx              ON compound_alerts (rule_id);
CREATE INDEX routes_destination_case_idx           ON routes (destination_case_id);
CREATE INDEX routes_destination_facility_idx       ON routes (destination_facility_id);
CREATE INDEX routes_invalidated_by_idx             ON routes (invalidated_by_alert_id);
CREATE INDEX responder_positions_incident_idx      ON responder_positions (incident_id);
CREATE INDEX responder_positions_mission_idx       ON responder_positions (mission_id);
CREATE INDEX responder_last_positions_incident_idx ON responder_last_positions (incident_id);
CREATE INDEX responder_last_positions_mission_idx  ON responder_last_positions (mission_id);
CREATE INDEX sos_alerts_user_idx                   ON sos_alerts (user_id);
CREATE INDEX sos_alerts_media_idx                  ON sos_alerts (media_id);
CREATE INDEX notifications_incident_idx            ON notifications (incident_id);
CREATE INDEX notifications_alert_idx               ON notifications (alert_id);
CREATE INDEX notifications_mission_idx             ON notifications (mission_id);
CREATE INDEX notifications_case_idx                ON notifications (case_id);
CREATE INDEX notifications_sos_idx                 ON notifications (sos_id);
CREATE INDEX notifications_route_idx               ON notifications (route_id);
CREATE INDEX reports_scope_zone_idx                ON reports (scope_zone_id);
CREATE INDEX reports_job_idx                       ON reports (job_id);
CREATE INDEX image_embeddings_model_idx            ON image_embeddings (model_id);
CREATE INDEX image_embeddings_building_idx         ON image_embeddings (building_id);
CREATE INDEX image_embeddings_image_idx            ON image_embeddings (image_id);
