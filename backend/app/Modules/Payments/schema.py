from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CreatePaymentIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: int | None = Field(default=None, ge=1)
    payment_method: str = Field(min_length=2, max_length=50)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency_code: str = Field(default="KES", min_length=3, max_length=3)
    description: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=16, max_length=120)

    @field_validator("payment_method", "idempotency_key")
    @classmethod
    def clean_identifier(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value is required")
        return value

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()


class PaymentIntentResponse(BaseModel):
    public_id: str
    job_id: int | None
    amount: Decimal
    currency_code: str
    payment_method: str
    status: str
    provider_code: str | None
    provider_reference: str | None
    expires_at: datetime | None
    created_at: datetime


class PaymentTransactionResponse(BaseModel):
    public_id: str
    payment_intent_id: str
    transaction_type: str
    amount: Decimal
    currency_code: str
    status: str
    provider_code: str | None
    provider_transaction_id: str | None
    provider_reference: str | None
    created_at: datetime


class PaymentEventResponse(BaseModel):
    event_type: str
    provider_code: str | None
    provider_event_id: str | None
    created_at: datetime


class MPPesaCallbackRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Deliberately flexible: the provider adapter validates the provider-specific
    # callback contract instead of exposing provider fields in the core domain.
    payload: dict[str, Any]
