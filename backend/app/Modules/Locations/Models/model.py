from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class ProviderLocation:
    id: int
    provider_id: int
    latitude: float
    longitude: float
    address_line: str | None
    accuracy_meters: float | None
    is_primary: bool
    is_active: bool
