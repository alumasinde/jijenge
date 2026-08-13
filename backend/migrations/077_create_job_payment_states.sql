CREATE TABLE job_payment_statuses (
    id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
    code VARCHAR(60) NOT NULL,
    name VARCHAR(120) NOT NULL,
    is_terminal TINYINT(1) NOT NULL DEFAULT 0,
    is_success TINYINT(1) NOT NULL DEFAULT 0,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_job_payment_statuses_code (code),
    UNIQUE KEY uq_job_payment_statuses_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
INSERT INTO job_payment_statuses (code,name,is_terminal,is_success,sort_order) VALUES ('PENDING','Pending',0,0,10),('PROCESSING','Processing',0,0,20),('PAID','Paid',1,1,30),('FAILED','Failed',1,0,40),('CANCELLED','Cancelled',1,0,50),('REFUNDED','Refunded',1,0,60),('PARTIALLY_REFUNDED','Partially Refunded',1,0,70);
