from fastapi import HTTPException

from app.Modules.Trust.Repositories.trust_repository import TrustRepository


class TrustService:
    def __init__(self):
        self.repository = TrustRepository()

    def create_report(self, user_id, data):
        try:
            if data.reported_user_id == user_id:
                raise HTTPException(
                    status_code=422,
                    detail="You cannot report yourself",
                )
            return self.repository.create_report(user_id, data)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
