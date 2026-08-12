from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    body: str
    entity_type: str | None
    entity_id: int | None
    data: dict[str, Any] | None
    read_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class RegisterDeviceTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: str = Field(min_length=2, max_length=30)
    token: str = Field(min_length=10, max_length=500)
    device_name: str | None = Field(default=None, max_length=180)
    app_version: str | None = Field(default=None, max_length=50)


class MarkReadResponse(BaseModel):
    success: bool
