ALTER TABLE match_candidate_statuses
    ADD COLUMN sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0 AFTER name;

UPDATE match_candidate_statuses
SET sort_order = CASE code
    WHEN 'ELIGIBLE' THEN 10
    WHEN 'NOTIFIED' THEN 20
    WHEN 'DECLINED' THEN 30
    WHEN 'EXPIRED' THEN 40
    WHEN 'SELECTED' THEN 50
    WHEN 'INELIGIBLE' THEN 60
    ELSE 100
END;

ALTER TABLE job_match_candidates
    ADD COLUMN notified_at TIMESTAMP NULL AFTER generated_at,
    ADD COLUMN viewed_at TIMESTAMP NULL AFTER notified_at,
    ADD COLUMN responded_at TIMESTAMP NULL AFTER viewed_at,
    ADD COLUMN decline_reason VARCHAR(500) NULL AFTER responded_at,
    ADD KEY idx_job_match_candidates_response (
        provider_id, status_id, responded_at, id
    );
