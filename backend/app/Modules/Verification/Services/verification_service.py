from fastapi import HTTPException

from app.Modules.Verification.Repositories.verification_repository import (
    VerificationRepository,
)


class VerificationService:
    def __init__(self):
        self.repository = VerificationRepository()

    def create_request(self, user_id: int, verification_type_code: str):
        try:
            return self.repository.create_request(
                user_id,
                verification_type_code.strip().upper(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    def add_document(self, user_id: int, request_id: int, data):
        try:
            return self.repository.add_document(user_id, request_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    def list_requests(self, user_id: int):
        return self.repository.list_requests(user_id)
