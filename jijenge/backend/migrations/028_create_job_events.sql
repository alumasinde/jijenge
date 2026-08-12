CREATE TABLE job_events (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
 job_id BIGINT UNSIGNED NOT NULL,
 event_type VARCHAR(80) NOT NULL,
 actor_user_id BIGINT UNSIGNED NOT NULL,
 from_status_id SMALLINT UNSIGNED NULL,
 to_status_id SMALLINT UNSIGNED NULL,
 metadata_json JSON NULL,
 notes VARCHAR(2000) NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (id),
 KEY idx_job_events_job_created (job_id,created_at,id),
 KEY idx_job_events_actor_created (actor_user_id,created_at),
 KEY idx_job_events_type_created (event_type,created_at),
 CONSTRAINT fk_job_events_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON UPDATE RESTRICT ON DELETE CASCADE,
 CONSTRAINT fk_job_events_actor FOREIGN KEY (actor_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 CONSTRAINT fk_job_events_from_status FOREIGN KEY (from_status_id) REFERENCES job_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 CONSTRAINT fk_job_events_to_status FOREIGN KEY (to_status_id) REFERENCES job_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
