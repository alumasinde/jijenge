ALTER TABLE sessions
    DROP INDEX uq_sessions_access_token_hash,
    DROP COLUMN access_token_hash;
