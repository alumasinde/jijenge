CREATE OR REPLACE VIEW v_financial_summary AS
SELECT
    fle.currency_code,
    SUM(CASE WHEN let.code='CUSTOMER_PAYMENT' AND fle.direction='CREDIT' THEN fle.amount ELSE 0 END) AS customer_payments,
    SUM(CASE WHEN let.code='PLATFORM_COMMISSION' AND fle.direction='CREDIT' THEN fle.amount ELSE 0 END) AS platform_commission,
    SUM(CASE WHEN let.code='PROVIDER_EARNING' AND fle.direction='CREDIT' THEN fle.amount ELSE 0 END) AS provider_earnings,
    SUM(CASE WHEN let.code='REFUND' AND fle.direction='DEBIT' THEN fle.amount ELSE 0 END) AS refunds,
    SUM(CASE WHEN let.code='PAYOUT' AND fle.direction='DEBIT' THEN fle.amount ELSE 0 END) AS payouts,
    SUM(CASE WHEN let.code='PAYOUT_REVERSAL' AND fle.direction='CREDIT' THEN fle.amount ELSE 0 END) AS payout_reversals,
    SUM(CASE WHEN let.code='REFUND_REVERSAL' AND fle.direction='CREDIT' THEN fle.amount ELSE 0 END) AS refund_reversals
FROM financial_ledger_entries fle
INNER JOIN ledger_entry_types let ON let.id=fle.entry_type_id
GROUP BY fle.currency_code;
