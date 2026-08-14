CREATE TABLE service_categories (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
 name VARCHAR(120) NOT NULL, slug VARCHAR(140) NOT NULL, parent_id BIGINT UNSIGNED NULL,
 PRIMARY KEY(id), UNIQUE KEY uq_service_category_name(name), UNIQUE KEY uq_service_category_slug(slug),
 KEY idx_service_category_parent(parent_id),
 CONSTRAINT fk_service_category_parent FOREIGN KEY(parent_id) REFERENCES service_categories(id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE provider_profiles (
 user_id BIGINT UNSIGNED NOT NULL,
 display_name VARCHAR(200) NOT NULL, bio VARCHAR(2000) NULL,
 service_radius_km DECIMAL(7,2) NOT NULL DEFAULT 10.00, verified BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
 PRIMARY KEY(user_id), CONSTRAINT fk_provider_profile_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT chk_provider_radius CHECK(service_radius_km>=0 AND service_radius_km<=500)
) ENGINE=InnoDB;

CREATE TABLE provider_locations (
 user_id BIGINT UNSIGNED NOT NULL,
 country VARCHAR(100) NOT NULL, county VARCHAR(100) NULL, city VARCHAR(100) NULL, area VARCHAR(150) NULL,
 latitude DECIMAL(10,7) NOT NULL, longitude DECIMAL(10,7) NOT NULL, updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
 PRIMARY KEY(user_id), KEY idx_provider_location_lat_lon(latitude,longitude),
 CONSTRAINT fk_provider_location_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT chk_provider_lat CHECK(latitude BETWEEN -90 AND 90), CONSTRAINT chk_provider_lon CHECK(longitude BETWEEN -180 AND 180)
) ENGINE=InnoDB;

CREATE TABLE service_listings (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, public_id CHAR(26) NOT NULL, provider_user_id BIGINT UNSIGNED NOT NULL,
 category_id BIGINT UNSIGNED NOT NULL, title VARCHAR(200) NOT NULL, description VARCHAR(5000) NOT NULL,
 starting_price_cents BIGINT UNSIGNED NOT NULL DEFAULT 0, currency CHAR(3) NOT NULL, status VARCHAR(16) NOT NULL DEFAULT 'active',
 created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
 PRIMARY KEY(id), UNIQUE KEY uq_service_listing_public(public_id), KEY idx_service_listing_category_status(category_id,status,created_at),
 KEY idx_service_listing_provider(provider_user_id,status),
 CONSTRAINT fk_service_listing_provider FOREIGN KEY(provider_user_id) REFERENCES users(id) ON DELETE CASCADE,
 CONSTRAINT fk_service_listing_category FOREIGN KEY(category_id) REFERENCES service_categories(id) ON DELETE RESTRICT,
 CONSTRAINT chk_service_listing_status CHECK(status IN ('draft','active','paused')),
 CONSTRAINT chk_service_listing_currency CHECK(currency REGEXP '^[A-Z]{3}$')
) ENGINE=InnoDB;

ALTER TABLE tasks ADD COLUMN service_id BIGINT UNSIGNED NULL AFTER category_id,
 ADD COLUMN country VARCHAR(100) NULL AFTER currency,
 ADD COLUMN county VARCHAR(100) NULL AFTER country,
 ADD COLUMN city VARCHAR(100) NULL AFTER county,
 ADD COLUMN area VARCHAR(150) NULL AFTER city,
 ADD COLUMN latitude DECIMAL(10,7) NULL AFTER area,
 ADD COLUMN longitude DECIMAL(10,7) NULL AFTER latitude,
 ADD KEY idx_tasks_location_status(latitude,longitude,status),
 ADD KEY idx_tasks_service_status(service_id,status,created_at),
 ADD CONSTRAINT fk_tasks_service FOREIGN KEY(service_id) REFERENCES service_listings(id) ON DELETE SET NULL,
 ADD CONSTRAINT chk_task_lat CHECK(latitude IS NULL OR latitude BETWEEN -90 AND 90),
 ADD CONSTRAINT chk_task_lon CHECK(longitude IS NULL OR longitude BETWEEN -180 AND 180);

CREATE TABLE ratings (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, assignment_id BIGINT UNSIGNED NOT NULL,
 reviewer_user_id BIGINT UNSIGNED NOT NULL, reviewee_user_id BIGINT UNSIGNED NOT NULL,
 score TINYINT UNSIGNED NOT NULL, comment VARCHAR(2000) NULL, status VARCHAR(16) NOT NULL DEFAULT 'published',
 created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 PRIMARY KEY(id), UNIQUE KEY uq_rating_assignment(assignment_id),
 KEY idx_rating_reviewee_status(reviewee_user_id,status,created_at),
 CONSTRAINT fk_rating_assignment FOREIGN KEY(assignment_id) REFERENCES task_assignments(id) ON DELETE RESTRICT,
 CONSTRAINT fk_rating_reviewer FOREIGN KEY(reviewer_user_id) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT fk_rating_reviewee FOREIGN KEY(reviewee_user_id) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT chk_rating_score CHECK(score BETWEEN 1 AND 5),
 CONSTRAINT chk_rating_status CHECK(status IN ('published','hidden','removed')),
 CONSTRAINT chk_rating_no_self CHECK(reviewer_user_id<>reviewee_user_id)
) ENGINE=InnoDB;

CREATE TABLE settlements (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, public_id CHAR(26) NOT NULL,
 task_id BIGINT UNSIGNED NOT NULL, assignment_id BIGINT UNSIGNED NOT NULL,
 payer_user_id BIGINT UNSIGNED NOT NULL, payee_user_id BIGINT UNSIGNED NOT NULL,
 method VARCHAR(24) NOT NULL, amount_cents BIGINT UNSIGNED NOT NULL, currency CHAR(3) NOT NULL,
 status VARCHAR(16) NOT NULL DEFAULT 'pending', claimed_by BIGINT UNSIGNED NULL, confirmed_by BIGINT UNSIGNED NULL,
 confirmed_at TIMESTAMP(6) NULL, created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
 updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
 PRIMARY KEY(id), UNIQUE KEY uq_settlement_public(public_id), UNIQUE KEY uq_settlement_assignment(assignment_id),
 KEY idx_settlement_status(status,created_at),
 CONSTRAINT fk_settlement_task FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE RESTRICT,
 CONSTRAINT fk_settlement_assignment FOREIGN KEY(assignment_id) REFERENCES task_assignments(id) ON DELETE RESTRICT,
 CONSTRAINT fk_settlement_payer FOREIGN KEY(payer_user_id) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT fk_settlement_payee FOREIGN KEY(payee_user_id) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT fk_settlement_claimed FOREIGN KEY(claimed_by) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT fk_settlement_confirmed FOREIGN KEY(confirmed_by) REFERENCES users(id) ON DELETE RESTRICT,
 CONSTRAINT chk_settlement_method CHECK(method IN ('platform','cash','mobile_money','bank_transfer','other')),
 CONSTRAINT chk_settlement_status CHECK(status IN ('pending','claimed','confirmed','disputed','cancelled')),
 CONSTRAINT chk_settlement_amount CHECK(amount_cents>0),
 CONSTRAINT chk_settlement_currency CHECK(currency REGEXP '^[A-Z]{3}$'),
 CONSTRAINT chk_settlement_no_self CHECK(payer_user_id<>payee_user_id)
) ENGINE=InnoDB;
