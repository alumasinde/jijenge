import hashlib
import json
import uuid

from app.database import db_connection


class WebhookService:
    def _status(self,cursor,code):
        cursor.execute(
            "SELECT id FROM payment_provider_event_statuses WHERE code=%s LIMIT 1",
            (code,),
        )
        row=cursor.fetchone()
        if not row: raise RuntimeError(f"Provider event status {code} missing")
        return int(row["id"])

    def receive(self, provider_code, provider_event_id, event_type,
                payload, payment_intent_id=None, payment_transaction_id=None):
        payload_hash=hashlib.sha256(
            json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest()

        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    SELECT id
                    FROM payment_provider_events
                    WHERE provider_code=%s AND provider_event_id=%s
                    LIMIT 1
                    """,
                    (provider_code,provider_event_id),
                )
                if cursor.fetchone():
                    connection.commit();cursor.close()
                    return {"duplicate":True}

                cursor.execute(
                    """
                    INSERT INTO payment_provider_events
                    (
                        public_id,provider_code,provider_event_id,
                        event_type,status_id,payment_intent_id,
                        payment_transaction_id,payload_hash,payload_json
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        str(uuid.uuid4()),provider_code,provider_event_id,
                        event_type,self._status(cursor,"RECEIVED"),
                        payment_intent_id,payment_transaction_id,
                        payload_hash,json.dumps(payload),
                    ),
                )
                event_id=int(cursor.lastrowid)
                connection.commit()
            except Exception:
                connection.rollback();cursor.close();raise
            cursor.close()
        return {"duplicate":False,"event_id":event_id}
