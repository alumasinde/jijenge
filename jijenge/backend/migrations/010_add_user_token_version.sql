ALTER TABLE users
    ADD COLUMN token_version VARCHAR(100) NOT NULL DEFAULT 'initial'
    AFTER password_hash;

ALTER TABLE users
    ADD KEY idx_users_token_version (token_version);
