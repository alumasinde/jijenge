ALTER TABLE sessions
    ADD COLUMN access_token_hash BINARY(32) NULL AFTER token_hash,
    ADD UNIQUE KEY uq_sessions_access_token_hash (access_token_hash);
