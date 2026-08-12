from app.Modules.Providers.Services.provider_service import ProviderService


class ProviderController:
    def __init__(self):
        self.service = ProviderService()

    def get_profile(self, user_id):
        return self.service.get_profile(user_id)

    def onboard(self, user_id, data):
        return self.service.onboard(user_id, data)

    def update_profile(self, user_id, data):
        return self.service.update_profile(user_id, data)

    def add_service(self, user_id, data):
        return self.service.add_service(user_id, data)

    def list_services(self, user_id):
        return self.service.list_services(user_id)

    def discover(self, service_id, latitude, longitude, radius_km, limit, verified_only):
        return self.service.discover(
            service_id, latitude, longitude, radius_km, limit, verified_only
        )
