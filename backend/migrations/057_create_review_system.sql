CREATE TABLE review_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255) NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_public TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uq_review_statuses_code (code),
    UNIQUE KEY uq_review_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO review_statuses
    (code, name, description, is_terminal, is_public, sort_order)
VALUES
('PENDING', 'Pending', 'Review is awaiting moderation/processing.', 0, 0, 10),
('PUBLISHED', 'Published', 'Review is visible publicly.', 1, 1, 20),
('HIDDEN', 'Hidden', 'Review is not publicly visible.', 1, 0, 30),
('REMOVED', 'Removed', 'Review was removed for a policy reason.', 1, 0, 40);

CREATE TABLE review_directions (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    reviewer_type VARCHAR(50) NOT NULL,
    reviewee_type VARCHAR(50) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,

    PRIMARY KEY (id),
    UNIQUE KEY uq_review_directions_code (code),
    UNIQUE KEY uq_review_directions_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO review_directions
    (code, name, reviewer_type, reviewee_type)
VALUES
('CUSTOMER_TO_PROVIDER', 'Customer to Provider', 'CUSTOMER', 'PROVIDER'),
('PROVIDER_TO_CUSTOMER', 'Provider to Customer', 'PROVIDER', 'CUSTOMER');

CREATE TABLE review_rating_dimensions (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NULL,
    applies_to VARCHAR(50) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    UNIQUE KEY uq_review_rating_dimensions_code (code),
    UNIQUE KEY uq_review_rating_dimensions_name (name),
    KEY idx_review_rating_dimensions_target_active (
        applies_to, is_active, sort_order
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO review_rating_dimensions
    (code, name, description, applies_to, sort_order)
VALUES
('OVERALL', 'Overall', 'Overall experience.', 'BOTH', 10),
('QUALITY', 'Quality', 'Quality of work or service.', 'PROVIDER', 20),
('COMMUNICATION', 'Communication', 'Communication and responsiveness.', 'BOTH', 30),
('PUNCTUALITY', 'Punctuality', 'Timeliness and reliability.', 'PROVIDER', 40),
('PROFESSIONALISM', 'Professionalism', 'Professional conduct.', 'BOTH', 50);

CREATE TABLE reviews (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(36) NOT NULL,
    job_id BIGINT UNSIGNED NOT NULL,
    reviewer_user_id BIGINT UNSIGNED NOT NULL,
    reviewee_user_id BIGINT UNSIGNED NOT NULL,
    direction_id SMALLINT UNSIGNED NOT NULL,
    status_id SMALLINT UNSIGNED NOT NULL,
    title VARCHAR(180) NULL,
    body VARCHAR(3000) NULL,
    overall_rating TINYINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    published_at TIMESTAMP NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_reviews_public_id (public_id),
    UNIQUE KEY uq_reviews_job_reviewer_reviewee (
        job_id, reviewer_user_id, reviewee_user_id
    ),
    KEY idx_reviews_reviewee_status_created (
        reviewee_user_id, status_id, created_at
    ),
    KEY idx_reviews_job_status_created (
        job_id, status_id, created_at
    ),
    KEY idx_reviews_reviewer_created (
        reviewer_user_id, created_at
    ),

    CONSTRAINT fk_reviews_job
        FOREIGN KEY (job_id)
        REFERENCES jobs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_reviews_reviewer
        FOREIGN KEY (reviewer_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_reviews_reviewee
        FOREIGN KEY (reviewee_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_reviews_direction
        FOREIGN KEY (direction_id)
        REFERENCES review_directions (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT fk_reviews_status
        FOREIGN KEY (status_id)
        REFERENCES review_statuses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_reviews_rating
        CHECK (overall_rating BETWEEN 1 AND 5),

    CONSTRAINT chk_reviews_different_users
        CHECK (reviewer_user_id <> reviewee_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE review_dimension_scores (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    review_id BIGINT UNSIGNED NOT NULL,
    dimension_id SMALLINT UNSIGNED NOT NULL,
    score TINYINT UNSIGNED NOT NULL,

    PRIMARY KEY (id),
    UNIQUE KEY uq_review_dimension_score (review_id, dimension_id),
    KEY idx_review_dimension_scores_dimension (dimension_id, score),

    CONSTRAINT fk_review_dimension_scores_review
        FOREIGN KEY (review_id)
        REFERENCES reviews (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_review_dimension_scores_dimension
        FOREIGN KEY (dimension_id)
        REFERENCES review_rating_dimensions (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT chk_review_dimension_scores_score
        CHECK (score BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE provider_rating_summaries (
    provider_user_id BIGINT UNSIGNED NOT NULL,
    published_review_count INT UNSIGNED NOT NULL DEFAULT 0,
    overall_rating_sum DECIMAL(14,2) NOT NULL DEFAULT 0,
    overall_rating_average DECIMAL(4,2) NULL,
    quality_average DECIMAL(4,2) NULL,
    communication_average DECIMAL(4,2) NULL,
    punctuality_average DECIMAL(4,2) NULL,
    professionalism_average DECIMAL(4,2) NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (provider_user_id),

    CONSTRAINT fk_provider_rating_summaries_user
        FOREIGN KEY (provider_user_id)
        REFERENCES users (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
