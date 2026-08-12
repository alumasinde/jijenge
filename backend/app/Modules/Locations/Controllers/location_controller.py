from app.Modules.Locations.Services.location_service import LocationService


class LocationController:
    def __init__(self):
        self.service = LocationService()

    def set_provider_location(self, provider_id: int, data):
        return self.service.set_provider_location(provider_id, data)

    def list_provider_locations(self, provider_id: int):
        return self.service.list_provider_locations(provider_id)

    def add_service_area(self, provider_id: int, data):
        return self.service.add_service_area(provider_id, data)

    def list_service_areas(self, provider_id: int):
        return self.service.list_service_areas(provider_id)

    def nearby_providers(
        self, service_id: int, latitude: float, longitude: float,
        radius_km: float, limit: int
    ):
        return self.service.nearby_providers(
            service_id, latitude, longitude, radius_km, limit
        )

    def nearby_providers_by_service_area(
        self, service_id: int, latitude: float, longitude: float, limit: int
    ):
        return self.service.nearby_providers_by_service_area(
            service_id, latitude, longitude, limit
        )
