from fastapi import HTTPException, status

from app.Modules.PublicContent.Repositories.public_content_repository import PublicContentRepository


class PublicContentService:
    def __init__(self):
        self.repository = PublicContentRepository()

    def get_public(self, locale: str):
        return self.repository.get_public(locale)

    def list_admin(self, locale: str | None, active_only: bool, search: str | None):
        return self.repository.list_admin(locale, active_only, search)

    def create(self, data):
        try:
            return self.repository.create(data.model_dump())
        except Exception as exc:
            if getattr(exc, "errno", None) == 1062:
                raise HTTPException(status_code=409, detail="Content key already exists for this locale") from exc
            raise

    def update(self, content_id: int, data):
        try:
            result = self.repository.update(content_id, data.model_dump())
        except Exception as exc:
            if getattr(exc, "errno", None) == 1062:
                raise HTTPException(status_code=409, detail="Content key already exists for this locale") from exc
            raise
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public content not found")
        return result

    def delete(self, content_id: int):
        if not self.repository.delete(content_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public content not found")
