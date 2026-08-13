from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


ContentType = Literal["text", "json", "number", "boolean"]


class PublicContentWriteRequest(BaseModel):
    content_key: str = Field(min_length=1, max_length=160)
    locale: str = Field(min_length=2, max_length=20)
    content_type: ContentType
    content_value: Any
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0, le=2_147_483_647)

    @field_validator("content_key")
    @classmethod
    def validate_key(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ch.isspace() for ch in value) or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for ch in value):
            raise ValueError("content_key may only contain letters, numbers, dots, underscores, and hyphens")
        return value

    @field_validator("locale")
    @classmethod
    def validate_locale(cls, value: str) -> str:
        return value.strip()


class PublicContentResponse(BaseModel):
    id: int
    content_key: str
    locale: str
    content_type: ContentType
    value: Any
    is_active: bool
    sort_order: int
    created_at: Any = None
    updated_at: Any = None
