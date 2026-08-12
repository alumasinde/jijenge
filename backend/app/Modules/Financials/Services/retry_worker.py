from app.database import db_connection
from app.Modules.Financials.Services.execution_service import FinancialExecutionService


class RetryWorker:
    def run(self, limit=50):
        service=FinancialExecutionService()
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT fe.id,fe.execution_type
                FROM financial_executions fe
                INNER JOIN financial_execution_statuses fes
                    ON fes.id=fe.status_id
                WHERE fes.code='RETRYABLE'
                  AND (fe.next_attempt_at IS NULL
                       OR fe.next_attempt_at<=CURRENT_TIMESTAMP)
                ORDER BY fe.id
                LIMIT %s
                """,(limit,),
            )
            rows=cursor.fetchall();cursor.close()

        results=[]
        for row in rows:
            if row["execution_type"]=="PAYOUT":
                results.append(service.execute_settlement(row["id"]))
            elif row["execution_type"]=="REFUND":
                results.append(service.execute_refund(row["id"]))
        return results
