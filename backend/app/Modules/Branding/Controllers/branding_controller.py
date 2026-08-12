from app.Modules.Branding.Services.branding_service import BrandingService


class BrandingController:
    def __init__(self):
        self.service = BrandingService()

    def get_public(self):
        return self.service.get_public()

    def update_default(self, data):
        return self.service.update_default(data)
