import hashlib
import json

from fastapi import HTTPException, status

from app.Modules.Payments.Providers.registry import PaymentProviderRegistry
from app.config import settings
from app.Modules.Payments.Repositories.payment_repository import PaymentRepository
from app.Modules.Payments.schema import (
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentTransactionResponse,
)


class PaymentService:
    def __init__(self):
        self.repository = PaymentRepository()
        self.providers = PaymentProviderRegistry(settings)

    def _intent_response(self, row):
        return PaymentIntentResponse(
            public_id=row["public_id"],
            job_id=int(row["job_id"]) if row["job_id"] is not None else None,
            amount=row["amount"],
            currency_code=row["currency_code"],
            payment_method=row["payment_method"],
            status=row["status"],
            provider_code=row["provider_code"],
            provider_reference=row["provider_reference"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
        )

    def create_intent(self, user_id: int, data: CreatePaymentIntentRequest):
        if data.currency_code != "KES":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Only KES is currently supported",
            )

        try:
            row = self.repository.get_or_create_intent(
                payer_user_id=user_id,
                job_id=data.job_id,
                payment_method=data.payment_method.upper(),
                amount=data.amount,
                currency_code=data.currency_code,
                description=data.description,
                idempotency_key=data.idempotency_key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

        return self._intent_response(row)

    def initiate(self, user_id: int, intent_id: int, payer_reference: str | None):
        row = self.repository.begin_provider_request(user_id, intent_id)
        provider_code = row["provider_code"]

        if not provider_code:
            raise HTTPException(
                status_code=400,
                detail="Selected payment method has no external provider",
            )

        provider = self.providers.get(provider_code)

        try:
            if provider_code == "MPESA":
                if not payer_reference:
                    raise HTTPException(
                        status_code=422,
                        detail="A customer M-Pesa phone number is required",
                    )
                result = provider.initiate_customer_payment(
                    amount=row["amount"],
                    currency_code=row["currency_code"],
                    payer_reference=payer_reference,
                    callback_url=settings.mpesa_callback_url,
                    idempotency_key=f"intent:{intent_id}",
                )
            elif provider_code == "CASH":
                result = provider.initiate_customer_payment(
                    amount=row["amount"],
                    currency_code=row["currency_code"],
                    payer_reference=payer_reference or "",
                    callback_url="",
                    idempotency_key=f"intent:{intent_id}",
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported payment provider: {provider_code}",
                )
        except HTTPException:
            raise
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Payment provider error: {exc}")

        if result.provider_reference:
            self.repository.save_provider_reference(
                user_id,
                intent_id,
                provider_code,
                result.provider_reference,
            )

        if provider_code == "CASH":
            self._ensure_cash_record(
                intent_id,user_id,row["amount"],row["currency_code"]
            )

        return {
            "accepted": result.status in {"SENT","PENDING_CONFIRMATION"},
            "status": result.status,
            "provider_code": provider_code,
            "provider_request_id": result.provider_request_id,
            "provider_reference": result.provider_reference,
            "message": result.message,
            "response": result.response,
        }

    def query_mpesa(self, user_id: int, intent_id: int):
        row=self.repository.get_intent_by_id(user_id,intent_id)
        if not row:
            raise HTTPException(status_code=404,detail="Payment intent not found")
        if row["provider_code"] != "MPESA" or not row["provider_reference"]:
            raise HTTPException(status_code=409,detail="M-Pesa CheckoutRequestID is not available")
        provider=self.providers.get("MPESA")
        try:
            return provider.query_stk(row["provider_reference"])
        except Exception as exc:
            raise HTTPException(status_code=502,detail=f"M-Pesa query failed: {exc}")

    def _ensure_cash_record(self, intent_id, payer_user_id, amount, currency_code):
        from uuid import uuid4
        from app.database import db_connection
        with db_connection() as connection:
            cursor=connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id FROM cash_payment_records
                WHERE payment_intent_id=%s LIMIT 1
                """,
                (intent_id,),
            )
            if cursor.fetchone():
                cursor.close()
                return
            cursor.execute(
                "SELECT id FROM cash_payment_statuses WHERE code='PENDING_CONFIRMATION' LIMIT 1"
            )
            status=cursor.fetchone()["id"]
            cursor.execute(
                """
                INSERT INTO cash_payment_records
                    (public_id,payment_intent_id,payer_user_id,status_id,
                     amount,currency_code)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (str(uuid4()),intent_id,payer_user_id,status,amount,currency_code),
            )
            connection.commit()
            cursor.close()

    def list_transactions(self, user_id: int, intent_id: int):
        return [
            PaymentTransactionResponse(
                public_id=row["public_id"],
                payment_intent_id=row["payment_intent_id"],
                transaction_type=row["transaction_type"],
                amount=row["amount"],
                currency_code=row["currency_code"],
                status=row["status"],
                provider_code=row["provider_code"],
                provider_transaction_id=row["provider_transaction_id"],
                provider_reference=row["provider_reference"],
                created_at=row["created_at"],
            )
            for row in self.repository.list_transactions(user_id, intent_id)
        ]

    def process_callback(
        self,
        *,
        intent_id: int,
        provider_code: str,
        provider_event_id: str | None,
        payload: dict,
        result_status: str,
        provider_transaction_id: str | None,
        provider_reference: str | None,
        response_message: str | None,
        callback_amount=None,
        callback_currency: str | None = None,
    ):
        payload_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode()
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        event_key = (
            f"{provider_code}:{provider_event_id}"
            if provider_event_id
            else f"{provider_code}:payload:{payload_hash}"
        )

        result = self.repository.record_callback(
            intent_id=intent_id,
            provider_code=provider_code,
            provider_event_id=provider_event_id,
            event_key=event_key,
            payload_hash=payload_hash,
            payload=payload,
            result_status=result_status,
            provider_transaction_id=provider_transaction_id,
            provider_reference=provider_reference,
            response_message=response_message,
            callback_amount=callback_amount,
            callback_currency=callback_currency,
        )

        if result_status == "SUCCEEDED" and not result.get("duplicate"):
            from app.Modules.Financials.Services.payment_success_service import PaymentSuccessService
            transaction_id = result.get("transaction_id")
            if transaction_id:
                PaymentSuccessService().finalize(
                    payment_intent_id=int(intent_id),
                    payment_transaction_id=int(transaction_id),
                )
        return result
