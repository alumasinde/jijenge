from fastapi import HTTPException, status

from app.Modules.Locations.Repositories.location_repository import LocationRepository
from app.Modules.Locations.schema import (
    JobLocationRequest,
    NearbyProviderResponse,
    ProviderLocationRequest,
    ProviderLocationResponse,
    ServiceAreaRequest,
    ServiceAreaResponse,
)


class LocationService:
    def __init__(self):
        self.repository = LocationRepository()

    def set_provider_location(
        self, provider_id: int, data: ProviderLocationRequest
    ) -> ProviderLocationResponse:
        row = self.repository.set_provider_location(
            provider_id=provider_id,
            latitude=data.latitude,
            longitude=data.longitude,
            address_line=data.address_line,
            accuracy_meters=data.accuracy_meters,
            is_primary=data.is_primary,
        )
        return ProviderLocationResponse(
            id=int(row["id"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            address_line=row["address_line"],
            accuracy_meters=(
                float(row["accuracy_meters"])
                if row["accuracy_meters"] is not None
                else None
            ),
            is_primary=bool(row["is_primary"]),
            is_active=bool(row["is_active"]),
        )

    def list_provider_locations(self, provider_id: int):
        return [
            ProviderLocationResponse(
                id=int(row["id"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                address_line=row["address_line"],
                accuracy_meters=(
                    float(row["accuracy_meters"])
                    if row["accuracy_meters"] is not None
                    else None
                ),
                is_primary=bool(row["is_primary"]),
                is_active=bool(row["is_active"]),
            )
            for row in self.repository.list_provider_locations(provider_id)
        ]

    def add_service_area(
        self, provider_id: int, data: ServiceAreaRequest
    ) -> ServiceAreaResponse:
        row = self.repository.add_service_area(
            provider_id=provider_id,
            latitude=data.latitude,
            longitude=data.longitude,
            radius_km=data.radius_km,
            name=data.name,
        )
        return ServiceAreaResponse(
            id=int(row["id"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            radius_km=float(row["radius_km"]),
            name=row["name"],
            is_active=bool(row["is_active"]),
        )

    def list_service_areas(self, provider_id: int):
        return [
            ServiceAreaResponse(
                id=int(row["id"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                radius_km=float(row["radius_km"]),
                name=row["name"],
                is_active=bool(row["is_active"]),
            )
            for row in self.repository.list_service_areas(provider_id)
        ]

    def nearby_providers(
        self,
        service_id: int,
        latitude: float,
        longitude: float,
        radius_km: float,
        limit: int,
    ):
        rows = self.repository.nearby_providers(
            service_id=service_id,
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
        )
        return [
            NearbyProviderResponse(
                provider_id=int(row["provider_id"]),
                distance_km=float(row["distance_km"]),
                business_name=row["business_name"],
                professional_title=row["professional_title"],
                is_verified=bool(row["is_verified"]),
            )
            for row in rows
        ]

    def nearby_providers_by_service_area(
        self,
        service_id: int,
        latitude: float,
        longitude: float,
        limit: int,
    ):
        rows = self.repository.nearby_providers_by_service_area(
            service_id=service_id,
            latitude=latitude,
            longitude=longitude,
            limit=limit,
        )
        return [
            NearbyProviderResponse(
                provider_id=int(row["provider_id"]),
                distance_km=float(row["center_distance_km"]),
                business_name=row["business_name"],
                professional_title=row["professional_title"],
                is_verified=bool(row["is_verified"]),
            )
            for row in rows
        ]
