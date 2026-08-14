ALTER TABLE task_assignments ADD UNIQUE KEY uq_task_assignments_task (task_id);
ALTER TABLE task_events ADD KEY idx_task_events_type_created (event_type, created_at);
