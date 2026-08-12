CREATE TABLE match_candidate_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_match_candidate_statuses_code (code),
    UNIQUE KEY uq_match_candidate_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO match_candidate_statuses (code, name, is_terminal) VALUES
('ELIGIBLE', 'Eligible', 0),
('NOTIFIED', 'Notified', 0),
('DECLINED', 'Declined', 1),
('EXPIRED', 'Expired', 1),
('SELECTED', 'Selected', 1),
('INELIGIBLE', 'Ineligible', 1);

CREATE TABLE job_match_candidates (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_id BIGINT UNSIGNED NOT NULL,
    provider_id BIGINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    distance_km DECIMAL(10,3) NOT NULL,
    within_service_area TINYINT(1) NOT NULL DEFAULT 0,
    available_for_job TINYINT(1) NOT NULL DEFAULT 0,
    verified TINYINT(1) NOT NULL DEFAULT 0,
    rating_average DECIMAL(4,2) NULL,
    experience_years DECIMAL(8,2) NULL,
    match_score DECIMAL(8,4) NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_job_match_candidates_job_provider (
        job_id, provider_id
    ),
    KEY idx_job_match_candidates_job_status_score (
        job_id, status_id, match_score DESC, id
    ),
    KEY idx_job_match_candidates_provider_status (
        provider_id, status_id, created_at
    ),

    CONSTRAINT fk_job_match_candidates_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_match_candidates_provider
        FOREIGN KEY (provider_id)
        REFERENCES provider_profiles (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_job_match_candidates_status
        FOREIGN KEY (status_id)
        REFERENCES match_candidate_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_job_match_candidates_distance
        CHECK (distance_km >= 0),

    CONSTRAINT chk_job_match_candidates_score
        CHECK (match_score >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
