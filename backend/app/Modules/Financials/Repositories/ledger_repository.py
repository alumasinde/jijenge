import uuid

from app.database import db_connection


class LedgerRepository:
    def post(
        self,
        *,
        reference_type: str,
        reference_id: int,
        payment_transaction_id: int | None,
        entry_type: str,
        currency_code: str,
        description: str | None,
        idempotency_key: str,
        lines: list[dict],
    ):
        if not lines:
            raise ValueError("Ledger transaction requires lines")

        debit_total = sum((line["debit"] for line in lines), 0)
        credit_total = sum((line["credit"] for line in lines), 0)

        if debit_total != credit_total:
            raise ValueError("Ledger transaction is not balanced")

        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, public_id
                    FROM ledger_transactions
                    WHERE idempotency_key = %s
                    LIMIT 1
                    """,
                    (idempotency_key,),
                )
                existing = cursor.fetchone()
                if existing:
                    connection.commit()
                    cursor.close()
                    return existing

                cursor.execute(
                    """
                    SELECT id
                    FROM ledger_entry_types
                    WHERE code = %s AND is_active = 1
                    LIMIT 1
                    """,
                    (entry_type,),
                )
                entry = cursor.fetchone()
                if not entry:
                    raise ValueError("Ledger entry type is unavailable")

                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO ledger_transactions
                        (
                            public_id, reference_type, reference_id,
                            payment_transaction_id, entry_type_id,
                            currency_code, description, idempotency_key
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        public_id, reference_type, reference_id,
                        payment_transaction_id, entry["id"],
                        currency_code, description, idempotency_key,
                    ),
                )
                transaction_id = cursor.lastrowid

                for line in lines:
                    if line["debit"] > 0 and line["credit"] > 0:
                        raise ValueError(
                            "A ledger line cannot contain both debit and credit"
                        )
                    if line["debit"] <= 0 and line["credit"] <= 0:
                        raise ValueError(
                            "A ledger line must contain a positive debit or credit"
                        )

                    cursor.execute(
                        """
                        INSERT INTO ledger_lines
                            (
                                ledger_transaction_id,
                                financial_account_id,
                                debit_amount,
                                credit_amount
                            )
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            transaction_id,
                            line["account_id"],
                            line["debit"],
                            line["credit"],
                        ),
                    )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return {
            "id": int(transaction_id),
            "public_id": public_id,
        }
