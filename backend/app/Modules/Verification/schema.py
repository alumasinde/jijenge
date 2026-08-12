from pydantic import BaseModel, ConfigDict, Field


class CreateVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_type_code: str = Field(min_length=2, max_length=60)


class VerificationRequestResponse(BaseModel):
    public_id: str
    verification_type: str
    status: str
    submitted_at: str | None
    reviewed_at: str | None
    rejection_reason: str | None
    expires_at: str | None


class VerificationDocumentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type_code: str = Field(min_length=2, max_length=60)
    storage_key: str = Field(min_length=1, max_length=500)
    original_filename: str | None = Field(default=None, max_length=255)
    mime_type: str = Field(min_length=3, max_length=120)
    file_size_bytes: int = Field(gt=0, le=20_000_000)
    sha256_hash: str | None = Field(default=None, min_length=64, max_length=64)
    document_number_masked: str | None = Field(default=None, max_length=120)
