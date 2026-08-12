from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class BrandingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    app_name: str = Field(min_length=1, max_length=150)
    short_name: str = Field(min_length=1, max_length=80)
    tagline: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=1000)
    logo_dark_url: str | None = Field(default=None, max_length=1000)
    favicon_url: str | None = Field(default=None, max_length=1000)
    primary_color: str = Field(default="#2563EB")
    secondary_color: str = Field(default="#1E40AF")
    accent_color: str = Field(default="#F59E0B")
    background_color: str = Field(default="#F8FAFC")
    surface_color: str = Field(default="#FFFFFF")
    text_color: str = Field(default="#0F172A")
    muted_color: str = Field(default="#64748B")
    border_color: str = Field(default="#E2E8F0")
    success_color: str = Field(default="#16A34A")
    warning_color: str = Field(default="#D97706")
    danger_color: str = Field(default="#DC2626")
    info_color: str = Field(default="#0284C7")
    font_family: str = Field(default="Inter, system-ui, sans-serif", min_length=1, max_length=150)
    border_radius: str = Field(default="0.75rem", min_length=1, max_length=20)
    dark_mode_enabled: bool = True
    dark_theme: dict[str, Any] | None = None

    @field_validator(
        "primary_color", "secondary_color", "accent_color", "background_color",
        "surface_color", "text_color", "muted_color", "border_color",
        "success_color", "warning_color", "danger_color", "info_color",
    )
    @classmethod
    def validate_color(cls, value: str) -> str:
        value = value.strip()
        if not HEX_COLOR.fullmatch(value):
            raise ValueError("Color must be a 6-digit hexadecimal value such as #2563EB")
        return value.upper()


class BrandingResponse(BrandingUpdateRequest):
    id: int
    brand_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PublicBrandingResponse(BrandingResponse):
    pass

