
CREATE TABLE audit_events (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    actor_user_id BIGINT UNSIGNED NULL,
    action VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128) NULL,
    request_id VARCHAR(128) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(512) NULL,
    outcome VARCHAR(16) NOT NULL DEFAULT 'success',
    reason VARCHAR(500) NULL,
    metadata JSON NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY(id),
    UNIQUE KEY uq_audit_events_public_id(public_id),
    KEY idx_audit_actor_created(actor_user_id,created_at,id),
    KEY idx_audit_resource_created(resource_type,resource_id,created_at,id),
    KEY idx_audit_request(request_id),
    CONSTRAINT fk_audit_actor FOREIGN KEY(actor_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT chk_audit_outcome CHECK(outcome IN ('success','failure','denied'))
) ENGINE=InnoDB;

CREATE TABLE reconciliation_runs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    public_id CHAR(26) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'running',
    accounts_checked BIGINT UNSIGNED NOT NULL DEFAULT 0,
    transactions_checked BIGINT UNSIGNED NOT NULL DEFAULT 0,
    discrepancies BIGINT UNSIGNED NOT NULL DEFAULT 0,
    started_at TIMESTAMP(6) NOT NULL,
    finished_at TIMESTAMP(6) NULL,
    PRIMARY KEY(id),
    UNIQUE KEY uq_reconciliation_runs_public_id(public_id),
    KEY idx_reconciliation_runs_status_started(status,started_at),
    CONSTRAINT chk_reconciliation_run_status CHECK(status IN ('running','completed','failed'))
) ENGINE=InnoDB;

CREATE TABLE reconciliation_issues (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_id BIGINT UNSIGNED NOT NULL,
    issue_type VARCHAR(64) NOT NULL,
    account_id BIGINT UNSIGNED NULL,
    transaction_id BIGINT UNSIGNED NULL,
    expected_cents BIGINT NOT NULL,
    actual_cents BIGINT NOT NULL,
    details VARCHAR(1000) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY(id),
    KEY idx_reconciliation_issues_run(run_id,id),
    KEY idx_reconciliation_issues_account(account_id,created_at),
    KEY idx_reconciliation_issues_transaction(transaction_id,created_at),
    CONSTRAINT fk_reconciliation_issue_run FOREIGN KEY(run_id) REFERENCES reconciliation_runs(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reconciliation_issue_account FOREIGN KEY(account_id) REFERENCES financial_accounts(id) ON DELETE RESTRICT,
    CONSTRAINT fk_reconciliation_issue_transaction FOREIGN KEY(transaction_id) REFERENCES ledger_transactions(id) ON DELETE RESTRICT
) ENGINE=InnoDB;
