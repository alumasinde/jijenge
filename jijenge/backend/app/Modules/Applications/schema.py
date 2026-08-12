from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    proposed_price: Decimal | None = Field(default=None, ge=0)
    message: str | None = Field(default=None, max_length=2000)
    estimated_start_at: datetime | None = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    provider_id: int
    status: str
    proposed_price: Decimal | None
    message: str | None
    estimated_start_at: datetime | None
    created_at: datetime
    updated_at: datetime
    responded_at: datetime | None


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int


class AssignmentResponse(BaseModel):
    id: int
    job_id: int
    provider_id: int
    application_id: int | None
    status: str
    assigned_by_user_id: int
    assigned_at: datetime
    confirmation_deadline: datetime | None
    confirmed_at: datetime | None
    declined_at: datetime | None
    decline_reason: str | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None


class AssignmentDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = Field(default=None, max_length=1000)


class CreateApplicationFeeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    payment_method: str = Field(min_length=2, max_length=50)
    idempotency_key: str = Field(min_length=16, max_length=160)


class ApplicationFeeResponse(BaseModel):
    id: int
    public_id: str
    application_id: int
    amount: Decimal
    currency_code: str
    payment_method: str
    status: str
    payment_intent_id: int | None
    payment_reference: str | None
    due_at: datetime | None
    paid_at: datetime | None
    payment_confirmed_at: datetime | None
