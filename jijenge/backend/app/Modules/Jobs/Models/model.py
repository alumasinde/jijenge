from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    id: int
    customer_id: int
    service_id: int
    status_code: str
    title: str
    description: str
