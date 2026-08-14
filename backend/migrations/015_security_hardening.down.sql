
DROP TABLE IF EXISTS security_events;
ALTER TABLE admin_action_requests DROP INDEX idx_admin_action_approval;
ALTER TABLE sessions DROP INDEX idx_sessions_expiry, DROP COLUMN last_rotated_at;
