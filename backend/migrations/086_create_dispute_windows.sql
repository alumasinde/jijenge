CREATE TABLE provider_earning_hold_reasons (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(70) NOT NULL,
    name VARCHAR(140) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_provider_earning_hold_reasons_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO provider_earning_hold_reasons (code,name) VALUES ('DISPUTE_WINDOW','Customer dispute window'),('DISPUTE_OPEN','Active dispute'),('MANUAL_REVIEW','Manual financial review'),('PAYOUT_REVIEW','Payout review');
CREATE TABLE provider_earning_holds (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    provider_earning_id BIGINT UNSIGNED NOT NULL,
    hold_reason_id SMALLINT UNSIGNED NOT NULL,
    starts_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    releases_at TIMESTAMP NULL,
    released_at TIMESTAMP NULL,
    released_by_user_id BIGINT UNSIGNED NULL,
    notes VARCHAR(2000) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_provider_earning_holds_release (released_at,releases_at,id),
    KEY idx_provider_earning_holds_earning (provider_earning_id,released_at,id),
    CONSTRAINT fk_provider_earning_holds_earning FOREIGN KEY (provider_earning_id) REFERENCES provider_earnings(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_earning_holds_reason FOREIGN KEY (hold_reason_id) REFERENCES provider_earning_hold_reasons(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT fk_provider_earning_holds_releaser FOREIGN KEY (released_by_user_id) REFERENCES users(id) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
