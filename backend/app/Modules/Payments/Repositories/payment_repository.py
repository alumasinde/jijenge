import json
import uuid

from app.database import db_connection


class PaymentRepository:
    def _status_id(self, cursor, code: str) -> int:
        cursor.execute(
            """
            SELECT id
            FROM payment_statuses
            WHERE code = %s AND is_active = 1
            LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Payment status {code} is missing")
        return int(row["id"])

    def _method(self, cursor, code: str):
        cursor.execute(
            """
            SELECT id, provider_code
            FROM payment_methods
            WHERE code = %s AND is_active = 1
            LIMIT 1
            """,
            (code,),
        )
        return cursor.fetchone()

    def get_or_create_intent(
        self,
        payer_user_id,
        job_id,
        payment_method,
        amount,
        currency_code,
        description,
        idempotency_key,
    ):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT
                        pi.id, pi.public_id, pi.job_id,
                        pi.amount, pi.currency_code,
                        pm.code AS payment_method,
                        ps.code AS status,
                        pi.provider_code,
                        pi.provider_reference,
                        pi.expires_at,
                        pi.created_at
                    FROM payment_intents pi
                    INNER JOIN payment_methods pm ON pm.id = pi.payment_method_id
                    INNER JOIN payment_statuses ps ON ps.id = pi.payment_status_id
                    WHERE pi.payer_user_id = %s
                      AND pi.idempotency_key = %s
                    LIMIT 1
                    """,
                    (payer_user_id, idempotency_key),
                )
                existing = cursor.fetchone()
                if existing:
                    # Idempotency means the same request key returns the original
                    # resource rather than creating a second payment.
                    if (
                        str(existing["amount"]) != str(amount)
                        or existing["currency_code"] != currency_code
                        or existing["payment_method"] != payment_method
                        or existing["job_id"] != job_id
                    ):
                        raise ValueError(
                            "Idempotency key was already used with different payment data"
                        )
                    cursor.close()
                    return existing

                method = self._method(cursor, payment_method)
                if not method:
                    raise ValueError("Payment method is not available")

                created_status = self._status_id(cursor, "CREATED")
                public_id = str(uuid.uuid4())

                cursor.execute(
                    """
                    INSERT INTO payment_intents
                        (
                            public_id, job_id, payer_user_id,
                            payment_method_id, payment_status_id,
                            currency_code, amount, description,
                            idempotency_key, provider_code,
                            expires_at
                        )
                    VALUES
                        (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 15 MINUTE)
                        )
                    """,
                    (
                        public_id, job_id, payer_user_id,
                        method["id"], created_status,
                        currency_code, amount, description,
                        idempotency_key, method["provider_code"],
                    ),
                )
                intent_id = int(cursor.lastrowid)

                event_type_id = self._payment_event_type_id(
                    cursor, "PAYMENT_CREATED"
                )
                event_key = f"payment:{intent_id}:created"
                cursor.execute(
                    """
                    INSERT INTO payment_events
                        (
                            payment_intent_id,
                            payment_event_type_id,
                            event_key
                        )
                    VALUES (%s, %s, %s)
                    """,
                    (intent_id, event_type_id, event_key),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()

        return self.get_intent_by_id(payer_user_id, intent_id)

    def _payment_event_type_id(self, cursor, code: str) -> int:
        cursor.execute(
            """
            SELECT id
            FROM payment_event_types
            WHERE code = %s AND is_active = 1
            LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Payment event type {code} is missing")
        return int(row["id"])

    def get_intent_by_id(self, payer_user_id, intent_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pi.id, pi.public_id, pi.job_id,
                    pi.amount, pi.currency_code,
                    pm.code AS payment_method,
                    ps.code AS status,
                    pi.provider_code,
                    pi.provider_reference,
                    pi.expires_at,
                    pi.created_at
                FROM payment_intents pi
                INNER JOIN payment_methods pm ON pm.id = pi.payment_method_id
                INNER JOIN payment_statuses ps ON ps.id = pi.payment_status_id
                WHERE pi.id = %s
                  AND pi.payer_user_id = %s
                LIMIT 1
                """,
                (intent_id, payer_user_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row

    def begin_provider_request(self, payer_user_id, intent_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT
                        pi.id, pi.public_id, pi.amount, pi.currency_code,
                        pi.provider_code, pi.provider_reference,
                        ps.code AS status,
                        pi.expires_at
                    FROM payment_intents pi
                    INNER JOIN payment_statuses ps ON ps.id = pi.payment_status_id
                    WHERE pi.id = %s
                      AND pi.payer_user_id = %s
                    FOR UPDATE
                    """,
                    (intent_id, payer_user_id),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Payment intent not found")

                if row["status"] in {
                    "SUCCEEDED", "CANCELLED", "EXPIRED", "REFUNDED"
                }:
                    raise ValueError("Payment intent is not payable")

                pending_id = self._status_id(cursor, "PENDING")
                cursor.execute(
                    """
                    UPDATE payment_intents
                    SET payment_status_id = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (pending_id, intent_id),
                )

                event_type_id = self._payment_event_type_id(
                    cursor, "PAYMENT_PROVIDER_REQUESTED"
                )
                cursor.execute(
                    """
                    INSERT INTO payment_events
                        (
                            payment_intent_id,
                            payment_event_type_id,
                            event_key
                        )
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        created_at = created_at
                    """,
                    (
                        intent_id,
                        event_type_id,
                        f"payment:{intent_id}:provider-requested",
                    ),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
            return self.get_intent_by_id(payer_user_id, intent_id)

    def save_provider_reference(
        self, payer_user_id, intent_id, provider_code, provider_reference
    ):
        with db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE payment_intents
                SET provider_code = %s,
                    provider_reference = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND payer_user_id = %s
                """,
                (provider_code, provider_reference, intent_id, payer_user_id),
            )
            connection.commit()
            cursor.close()

    def get_intent_for_callback(self, intent_id):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id,amount,currency_code
                FROM payment_intents
                WHERE id=%s
                LIMIT 1
                """,(intent_id,),
            )
            row=cursor.fetchone()
            cursor.close()
            return row

    def find_intent_by_provider_reference(self, provider_code, provider_reference):
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id,payer_user_id,job_id,amount,currency_code
                FROM payment_intents
                WHERE provider_code=%s AND provider_reference=%s
                LIMIT 1
                """,
                (provider_code,provider_reference),
            )
            row=cursor.fetchone()
            cursor.close()
            return row

    def record_callback(
        self,
        *,
        intent_id,
        provider_code,
        provider_event_id,
        event_key,
        payload_hash,
        payload,
        result_status,
        provider_transaction_id,
        provider_reference,
        response_message,
        callback_amount=None,
        callback_currency=None,
    ):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                # Idempotent webhook receipt.
                cursor.execute(
                    """
                    INSERT INTO payment_webhook_receipts
                        (
                            provider_code, provider_event_id,
                            event_key, payload_hash,
                            signature_verified,
                            processing_status, payload_json
                        )
                    VALUES (%s, %s, %s, %s, 1, 'RECEIVED', %s)
                    ON DUPLICATE KEY UPDATE
                        id = LAST_INSERT_ID(id)
                    """,
                    (
                        provider_code,
                        provider_event_id,
                        event_key,
                        payload_hash,
                        json.dumps(payload),
                    ),
                )

                cursor.execute(
                    """
                    SELECT id, processing_status
                    FROM payment_webhook_receipts
                    WHERE event_key = %s
                    LIMIT 1
                    """,
                    (event_key,),
                )
                receipt = cursor.fetchone()

                if receipt["processing_status"] == "PROCESSED":
                    connection.commit()
                    cursor.close()
                    cursor.execute(
                        """
                        SELECT id
                        FROM payment_transactions
                        WHERE payment_intent_id=%s AND idempotency_key=%s
                        LIMIT 1
                        """,
                        (intent_id,event_key),
                    )
                    tx=cursor.fetchone()
                    return {
                        "duplicate": True,
                        "transaction_id": int(tx["id"]) if tx else None,
                    }

                status_id = self._status_id(cursor, result_status)

                # Provider transaction/reference are stored on payment_transactions;
                # payment_intents keep provider_reference for quick lookup.
                if provider_reference:
                    cursor.execute(
                        """
                        UPDATE payment_intents
                        SET provider_reference = %s,
                            provider_code = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (provider_reference, provider_code, intent_id),
                    )

                tx_type_id = self._transaction_type_id(cursor, "CHARGE")
                cursor.execute(
                    """
                    SELECT id
                    FROM payment_transactions
                    WHERE payment_intent_id = %s
                      AND idempotency_key = %s
                    LIMIT 1
                    """,
                    (intent_id, event_key),
                )
                existing_tx = cursor.fetchone()

                if not existing_tx:
                    tx_public_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO payment_transactions
                            (
                                public_id,
                                payment_intent_id,
                                payment_status_id,
                                transaction_type,
                                amount,
                                currency_code,
                                provider_code,
                                provider_transaction_id,
                                provider_reference,
                                provider_response_message,
                                idempotency_key,
                                raw_response_json,
                                processed_at
                            )
                        SELECT
                            %s,
                            pi.id,
                            %s,
                            'CHARGE',
                            COALESCE(%s, pi.amount),
                            COALESCE(%s, pi.currency_code),
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            CURRENT_TIMESTAMP
                        FROM payment_intents pi
                        WHERE pi.id = %s
                        """,
                        (
                            tx_public_id,
                            status_id,
                            callback_amount,
                            callback_currency,
                            provider_code,
                            provider_transaction_id,
                            provider_reference,
                            response_message,
                            event_key,
                            json.dumps(payload),
                            intent_id,
                        ),
                    )

                cursor.execute(
                    """
                    SELECT id
                    FROM payment_transactions
                    WHERE payment_intent_id = %s
                      AND idempotency_key = %s
                    LIMIT 1
                    """,
                    (intent_id, event_key),
                )
                transaction_row = cursor.fetchone()
                transaction_id = int(transaction_row["id"]) if transaction_row else None

                event_type = (
                    "PAYMENT_SUCCEEDED"
                    if result_status == "SUCCEEDED"
                    else "PAYMENT_FAILED"
                )
                event_type_id = self._payment_event_type_id(cursor, event_type)

                cursor.execute(
                    """
                    INSERT INTO payment_events
                        (
                            payment_intent_id,
                            payment_event_type_id,
                            provider_code,
                            provider_event_id,
                            event_key,
                            payload_hash,
                            payload_json,
                            processed_at
                        )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON DUPLICATE KEY UPDATE
                        processed_at = CURRENT_TIMESTAMP
                    """,
                    (
                        intent_id,
                        event_type_id,
                        provider_code,
                        provider_event_id,
                        event_key,
                        payload_hash,
                        json.dumps(payload),
                    ),
                )

                cursor.execute(
                    """
                    UPDATE payment_webhook_receipts
                    SET processing_status = 'PROCESSED',
                        processed_at = CURRENT_TIMESTAMP
                    WHERE event_key = %s
                    """,
                    (event_key,),
                )

                cursor.execute(
                    """
                    UPDATE payment_intents
                    SET payment_status_id = %s,
                        succeeded_at = CASE
                            WHEN %s = 'SUCCEEDED' THEN CURRENT_TIMESTAMP
                            ELSE succeeded_at
                        END,
                        failed_at = CASE
                            WHEN %s = 'FAILED' THEN CURRENT_TIMESTAMP
                            ELSE failed_at
                        END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (status_id, result_status, result_status, intent_id),
                )

                connection.commit()
            except Exception:
                connection.rollback()
                cursor.close()
                raise
            cursor.close()
            return {
                "duplicate": False,
                "transaction_id": transaction_id,
            }

    def _transaction_type_id(self, cursor, code: str) -> int:
        cursor.execute(
            """
            SELECT id
            FROM payment_transaction_types
            WHERE code = %s AND is_active = 1
            LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"Transaction type {code} is missing")
        return int(row["id"])

    def list_transactions(self, payer_user_id, intent_id):
        with db_connection() as connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    pt.public_id,
                    pi.public_id AS payment_intent_id,
                    pt.transaction_type,
                    pt.amount,
                    pt.currency_code,
                    ps.code AS status,
                    pt.provider_code,
                    pt.provider_transaction_id,
                    pt.provider_reference,
                    pt.created_at
                FROM payment_transactions pt
                INNER JOIN payment_intents pi
                    ON pi.id = pt.payment_intent_id
                INNER JOIN payment_statuses ps
                    ON ps.id = pt.payment_status_id
                WHERE pt.payment_intent_id = %s
                  AND pi.payer_user_id = %s
                ORDER BY pt.created_at DESC, pt.id DESC
                """,
                (intent_id, payer_user_id),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
