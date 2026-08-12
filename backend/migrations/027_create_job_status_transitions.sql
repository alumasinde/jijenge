CREATE TABLE job_status_transitions (
 id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
 from_status_id SMALLINT UNSIGNED NOT NULL,
 to_status_id SMALLINT UNSIGNED NOT NULL,
 actor_role_code VARCHAR(50) NOT NULL,
 requires_assignment TINYINT(1) NOT NULL DEFAULT 0,
 is_active TINYINT(1) NOT NULL DEFAULT 1,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 PRIMARY KEY (id),
 UNIQUE KEY uq_job_status_transition (from_status_id,to_status_id,actor_role_code),
 KEY idx_job_status_transition_from_role (from_status_id,actor_role_code,is_active),
 CONSTRAINT fk_job_status_transition_from FOREIGN KEY (from_status_id) REFERENCES job_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 CONSTRAINT fk_job_status_transition_to FOREIGN KEY (to_status_id) REFERENCES job_statuses(id) ON UPDATE RESTRICT ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'CUSTOMER',0 FROM job_statuses f JOIN job_statuses t WHERE f.code='OPEN' AND t.code='CANCELLED';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'CUSTOMER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='ASSIGNED' AND t.code='CANCELLED';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'PROVIDER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='ASSIGNED' AND t.code='ON_THE_WAY';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'PROVIDER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='ON_THE_WAY' AND t.code='IN_PROGRESS';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'PROVIDER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='IN_PROGRESS' AND t.code='COMPLETED';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'PROVIDER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='ASSIGNED' AND t.code='CANCELLED';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'PROVIDER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='ON_THE_WAY' AND t.code='CANCELLED';
INSERT INTO job_status_transitions (from_status_id,to_status_id,actor_role_code,requires_assignment)
SELECT f.id,t.id,'PROVIDER',1 FROM job_statuses f JOIN job_statuses t WHERE f.code='IN_PROGRESS' AND t.code='CANCELLED';
