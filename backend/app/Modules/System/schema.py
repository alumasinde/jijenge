from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SystemSettingUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: Any
    value_type: str = Field(default="string", pattern="^(string|integer|decimal|boolean|json)$")
    description: str | None = Field(default=None, max_length=500)
    is_public: bool = False

    @field_validator("value")
    @classmethod
    def value_present(cls, value: Any) -> Any:
        if value is None:
            raise ValueError("Setting value cannot be null")
        return value


class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    value: Any
    value_type: str
    description: str | None
    is_public: bool
    is_editable: bool
    created_at: datetime
    updated_at: datetime
