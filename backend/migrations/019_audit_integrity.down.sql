DROP INDEX idx_audit_event_hash ON audit_events;

ALTER TABLE audit_events
    DROP COLUMN event_hash,
    DROP COLUMN previous_hash;
