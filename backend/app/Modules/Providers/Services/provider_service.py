from fastapi import HTTPException, status

from app.Modules.Providers.Repositories.provider_repository import ProviderRepository
from app.Modules.Providers.schema import (
    AddProviderServiceRequest,
    ProviderDiscoveryResponse,
    ProviderOnboardingRequest,
    ProviderProfileResponse,
    ProviderServiceResponse,
)


class ProviderService:
    def __init__(self):
        self.repository = ProviderRepository()

    def _profile_response(self, row):
        return ProviderProfileResponse(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            status=row["status_code"],
            business_name=row["business_name"],
            professional_title=row["professional_title"],
            bio=row["bio"],
            years_experience=row["years_experience"],
            is_verified=bool(row["is_verified"]),
        )

    def get_profile(self, user_id):
        row = self.repository.get_profile_by_user(user_id)
        if not row:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        return self._profile_response(row)

    def onboard(self, user_id, data: ProviderOnboardingRequest):
        existing = self.repository.get_profile_by_user(user_id)
        if existing:
            raise HTTPException(status_code=409, detail="Provider profile already exists")
        return self._profile_response(
            self.repository.create_profile(
                user_id, data.business_name, data.professional_title,
                data.bio, data.years_experience
            )
        )

    def update_profile(self, user_id, data: ProviderOnboardingRequest):
        existing = self.repository.get_profile_by_user(user_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        return self._profile_response(
            self.repository.update_profile(
                user_id, data.business_name, data.professional_title,
                data.bio, data.years_experience
            )
        )

    def add_service(self, user_id, data: AddProviderServiceRequest):
        profile = self.repository.get_profile_by_user(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        if not self.repository.service_exists(data.service_id):
            raise HTTPException(status_code=404, detail="Service not found")
        self.repository.add_service(
            int(profile["id"]), data.service_id, data.years_experience,
            data.minimum_price, data.maximum_price
        )
        row = next(
            r for r in self.repository.list_services(int(profile["id"]))
            if int(r["service_id"]) == data.service_id
        )
        return ProviderServiceResponse(
            service_id=int(row["service_id"]),
            service_code=row["service_code"],
            service_name=row["service_name"],
            years_experience=row["years_experience"],
            minimum_price=row["minimum_price"],
            maximum_price=row["maximum_price"],
            is_active=bool(row["is_active"]),
        )

    def list_services(self, user_id):
        profile = self.repository.get_profile_by_user(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Provider profile not found")
        return [
            ProviderServiceResponse(
                service_id=int(r["service_id"]),
                service_code=r["service_code"],
                service_name=r["service_name"],
                years_experience=r["years_experience"],
                minimum_price=r["minimum_price"],
                maximum_price=r["maximum_price"],
                is_active=bool(r["is_active"]),
            )
            for r in self.repository.list_services(int(profile["id"]))
        ]

    def discover(self, service_id, latitude, longitude, radius_km, limit, verified_only):
        rows = self.repository.discover(
            service_id, latitude, longitude, radius_km, limit, verified_only
        )
        return [
            ProviderDiscoveryResponse(
                provider_id=int(r["provider_id"]),
                business_name=r["business_name"],
                professional_title=r["professional_title"],
                bio=r["bio"],
                years_experience=r["years_experience"],
                is_verified=bool(r["is_verified"]),
                distance_km=float(r["distance_km"]),
                services=(
                    r["service_names"].split(", ")
                    if r["service_names"] else []
                ),
            )
            for r in rows
        ]
