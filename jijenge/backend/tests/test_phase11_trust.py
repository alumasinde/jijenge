import pytest

from app.Modules.Reviews.schema import CreateReviewRequest
from app.Modules.Verification.schema import VerificationDocumentInput
from app.Modules.Trust.schema import CreateTrustReportRequest


def test_review_rating_bounds():
    with pytest.raises(ValueError):
        CreateReviewRequest(overall_rating=6)


def test_verification_document_size_limit():
    with pytest.raises(ValueError):
        VerificationDocumentInput(
            document_type_code="NATIONAL_ID",
            storage_key="private/abc",
            mime_type="image/jpeg",
            file_size_bytes=20_000_001,
        )


def test_trust_report_requires_reasonable_description():
    with pytest.raises(ValueError):
        CreateTrustReportRequest(
            report_type_code="FRAUD",
            description="short",
        )
