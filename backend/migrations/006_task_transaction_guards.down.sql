ALTER TABLE task_events DROP INDEX idx_task_events_type_created;
ALTER TABLE task_assignments DROP INDEX uq_task_assignments_task;
