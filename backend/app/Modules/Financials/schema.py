from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class CreateJobPaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payment_method: str = Field(min_length=2, max_length=50)
    idempotency_key: str = Field(min_length=16, max_length=160)


class JobPaymentResponse(BaseModel):
    id: int
    public_id: str
    assignment_id: int
    job_id: int
    amount: Decimal
    currency_code: str
    payment_method: str
    status: str
    payment_intent_id: int | None
    payment_reference: str | None
    paid_at: datetime | None
    failure_reason: str | None
