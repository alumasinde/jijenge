ALTER TABLE audit_events
    ADD COLUMN previous_hash CHAR(64) NULL AFTER created_at,
    ADD COLUMN event_hash CHAR(64) NULL AFTER previous_hash;

CREATE INDEX idx_audit_event_hash ON audit_events(event_hash);
