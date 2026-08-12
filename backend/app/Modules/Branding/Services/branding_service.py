from fastapi import HTTPException, status

from app.Modules.Branding.Repositories.branding_repository import BrandingRepository


class BrandingService:
    def __init__(self):
        self.repository = BrandingRepository()

    def get_public(self):
        branding = self.repository.get_active()
        if not branding:
            raise HTTPException(status_code=503, detail="Platform branding is not configured")
        return branding

    def update_default(self, data):
        return self.repository.upsert_default(data.model_dump())
