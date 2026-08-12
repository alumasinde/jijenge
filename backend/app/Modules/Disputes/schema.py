from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class OpenDisputeRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    reason: str = Field(min_length=2,max_length=70)
    description: str = Field(min_length=10,max_length=5000)
    disputed_amount: Decimal = Field(default=Decimal("0"),ge=0)


class ResolveDisputeRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    status: str = Field(min_length=5,max_length=60)
    resolved_amount: Decimal = Field(default=Decimal("0"),ge=0)
    notes: str | None = Field(default=None,max_length=5000)


class CreateRefundRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=5,max_length=2000)
    idempotency_key: str = Field(min_length=16,max_length=160)
    dispute_id: int | None = None
