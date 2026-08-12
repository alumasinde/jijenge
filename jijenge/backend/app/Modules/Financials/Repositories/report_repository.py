from app.database import db_connection


class FinancialReportRepository:
    def summary(self):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM v_financial_summary ORDER BY currency_code")
            rows=cursor.fetchall()
            cursor.close()
        return rows

    def payment_history(self, user_id, limit, offset):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pt.id,pt.amount,pt.currency_code,pt.provider_code,
                    pt.provider_reference,pt.provider_transaction_id,
                    pts.code AS status,pt.created_at,
                    pi.id AS payment_intent_id,pi.job_id
                FROM payment_transactions pt
                INNER JOIN payment_intents pi ON pi.id=pt.payment_intent_id
                INNER JOIN payment_transaction_statuses pts ON pts.id=pt.status_id
                WHERE pi.customer_id=%s
                ORDER BY pt.id DESC
                LIMIT %s OFFSET %s
                """,(user_id,limit,offset),
            )
            rows=cursor.fetchall();cursor.close()
        return rows

    def provider_statement(self, provider_id, limit, offset):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    fle.id,fle.amount,fle.currency_code,fle.direction,
                    let.code AS entry_type,fle.reference,
                    fle.description,fle.created_at,
                    fle.job_id,fle.assignment_id
                FROM financial_ledger_entries fle
                INNER JOIN ledger_entry_types let ON let.id=fle.entry_type_id
                LEFT JOIN provider_earnings pe
                    ON pe.id=fle.provider_earning_id
                LEFT JOIN provider_settlements ps
                    ON ps.id=fle.settlement_id
                WHERE pe.provider_id=%s OR ps.provider_id=%s
                ORDER BY fle.id DESC
                LIMIT %s OFFSET %s
                """,(provider_id,provider_id,limit,offset),
            )
            rows=cursor.fetchall();cursor.close()
        return rows

    def exceptions(self, limit, offset):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    prr.id,prr.payment_transaction_id,
                    prr.provider_code,prs.code AS status,
                    prr.mismatch_reason,prr.checked_at
                FROM payment_reconciliation_records prr
                INNER JOIN payment_reconciliation_statuses prs
                    ON prs.id=prr.status_id
                WHERE prs.code='EXCEPTION'
                ORDER BY prr.id DESC
                LIMIT %s OFFSET %s
                """,(limit,offset),
            )
            rows=cursor.fetchall();cursor.close()
        return rows

    def kpis(self):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM jobs) AS total_jobs,
                    (SELECT COUNT(*) FROM payment_transactions) AS total_payment_transactions,
                    (SELECT COUNT(*) FROM disputes d
                        INNER JOIN dispute_statuses s ON s.id=d.status_id
                        WHERE s.is_terminal=0) AS open_disputes,
                    (SELECT COUNT(*) FROM refunds r
                        INNER JOIN refund_statuses s ON s.id=r.status_id
                        WHERE s.is_terminal=0) AS pending_refunds,
                    (SELECT COUNT(*) FROM provider_settlements ps
                        INNER JOIN provider_settlement_statuses s ON s.id=ps.status_id
                        WHERE s.code IN ('REQUESTED','PROCESSING')) AS pending_settlements,
                    (SELECT COUNT(*) FROM payment_reconciliation_records prr
                        INNER JOIN payment_reconciliation_statuses s ON s.id=prr.status_id
                        WHERE s.code='EXCEPTION') AS reconciliation_exceptions
                """,
            )
            row=cursor.fetchone();cursor.close()
        return row
