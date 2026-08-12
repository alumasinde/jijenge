ALTER TABLE jobs
 ADD COLUMN cancellation_reason VARCHAR(1000) NULL AFTER cancelled_at,
 ADD COLUMN completion_notes VARCHAR(2000) NULL AFTER cancellation_reason;
