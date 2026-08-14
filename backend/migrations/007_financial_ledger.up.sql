CREATE TABLE financial_accounts (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    owner_user_id BIGINT UNSIGNED NULL,
    currency CHAR(3) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_financial_accounts_public_id (public_id),
    KEY idx_financial_accounts_owner_currency (owner_user_id,currency),
    CONSTRAINT fk_financial_accounts_owner FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT chk_financial_accounts_currency CHECK (currency REGEXP '^[A-Z]{3}$'),
    CONSTRAINT chk_financial_accounts_status CHECK (status IN ('active','frozen','closed'))
) ENGINE=InnoDB;

CREATE TABLE financial_balances (
    account_id BIGINT UNSIGNED NOT NULL,
    available_cents BIGINT UNSIGNED NOT NULL DEFAULT 0,
    held_cents BIGINT UNSIGNED NOT NULL DEFAULT 0,
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (account_id),
    CONSTRAINT fk_financial_balances_account FOREIGN KEY (account_id) REFERENCES financial_accounts(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE ledger_transactions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    currency CHAR(3) NOT NULL,
    description VARCHAR(500) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_ledger_transactions_public_id (public_id),
    UNIQUE KEY uq_ledger_transactions_idempotency (idempotency_key),
    KEY idx_ledger_transactions_created (created_at),
    CONSTRAINT chk_ledger_transactions_currency CHECK (currency REGEXP '^[A-Z]{3}$')
) ENGINE=InnoDB;

CREATE TABLE ledger_entries (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    transaction_id BIGINT UNSIGNED NOT NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    debit_cents BIGINT UNSIGNED NOT NULL DEFAULT 0,
    credit_cents BIGINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_ledger_entries_transaction (transaction_id),
    KEY idx_ledger_entries_account_created (account_id,created_at),
    CONSTRAINT fk_ledger_entries_transaction FOREIGN KEY (transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ledger_entries_account FOREIGN KEY (account_id) REFERENCES financial_accounts(id) ON DELETE RESTRICT,
    CONSTRAINT chk_ledger_entry_one_side CHECK (
        (debit_cents > 0 AND credit_cents = 0) OR
        (credit_cents > 0 AND debit_cents = 0)
    )
) ENGINE=InnoDB;

CREATE TABLE ledger_holds (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    account_id BIGINT UNSIGNED NOT NULL,
    reference VARCHAR(128) NOT NULL,
    amount_cents BIGINT UNSIGNED NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_ledger_holds_public_id (public_id),
    UNIQUE KEY uq_ledger_holds_reference (reference),
    KEY idx_ledger_holds_account_status (account_id,status),
    CONSTRAINT fk_ledger_holds_account FOREIGN KEY (account_id) REFERENCES financial_accounts(id) ON DELETE RESTRICT,
    CONSTRAINT chk_ledger_holds_status CHECK (status IN ('active','released','captured')),
    CONSTRAINT chk_ledger_holds_amount CHECK (amount_cents > 0)
) ENGINE=InnoDB;

CREATE TABLE ledger_idempotency (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    idempotency_key VARCHAR(128) NOT NULL,
    operation VARCHAR(64) NOT NULL,
    request_hash BINARY(32) NOT NULL,
    transaction_id BIGINT UNSIGNED NULL,
    response_code SMALLINT UNSIGNED NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_ledger_idempotency_key (idempotency_key),
    CONSTRAINT fk_ledger_idempotency_transaction FOREIGN KEY (transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- NOTE: no DELIMITER directive here. DELIMITER is a mysql-CLI-only
-- meta-command; it is not real SQL and is not understood by
-- database/sql or any programmatic MySQL driver (including this
-- project's own cmd/migrate tool). Sending it as part of a migration
-- previously caused cmd/migrate to fail with a syntax error and left
-- this migration permanently stuck in the "dirty" state. Multi-statement
-- trigger bodies work correctly over the wire protocol as long as the
-- connection is opened with multiStatements=true (see Core/Database
-- and the DB_DSN examples in .env.example / docker-compose*.yml) --
-- the server parses the semicolons inside BEGIN...END correctly without
-- any client-side delimiter switching.
CREATE TRIGGER ledger_entries_no_update
BEFORE UPDATE ON ledger_entries
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ledger entries are immutable';
END;

CREATE TRIGGER ledger_entries_no_delete
BEFORE DELETE ON ledger_entries
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ledger entries are immutable';
END;

CREATE TRIGGER ledger_transactions_no_update
BEFORE UPDATE ON ledger_transactions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ledger transactions are immutable';
END;

CREATE TRIGGER ledger_transactions_no_delete
BEFORE DELETE ON ledger_transactions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'ledger transactions are immutable';
END;
