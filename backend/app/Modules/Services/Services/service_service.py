from app.Modules.Services.Repositories.service_repository import ServiceRepository
from app.Modules.Services.schema import (
    ServiceCategoryResponse,
    ServiceListResponse,
    ServiceResponse,
)


class ServiceService:
    def __init__(self):
        self.repository = ServiceRepository()

    def list_categories(self) -> list[ServiceCategoryResponse]:
        return [
            ServiceCategoryResponse(
                id=int(row["id"]),
                code=row["code"],
                name=row["name"],
                description=row["description"],
            )
            for row in self.repository.list_categories()
        ]

    def list_services(self, category_id: int | None = None) -> ServiceListResponse:
        rows = self.repository.list_services(category_id)
        return ServiceListResponse(
            items=[
                ServiceResponse(
                    id=int(row["id"]),
                    category_id=int(row["category_id"]),
                    category_code=row["category_code"],
                    category_name=row["category_name"],
                    code=row["code"],
                    name=row["name"],
                    description=row["description"],
                )
                for row in rows
            ],
            total=len(rows),
        )
