from fastapi import APIRouter, Query

from app.Modules.Services.Controllers.service_controller import ServiceController
from app.Modules.Services.schema import (
    ServiceCategoryResponse,
    ServiceListResponse,
)

router = APIRouter(prefix="/services", tags=["Services"])
controller = ServiceController()


@router.get("/categories", response_model=list[ServiceCategoryResponse])
def list_categories():
    return controller.list_categories()


@router.get("", response_model=ServiceListResponse)
def list_services(
    category_id: int | None = Query(default=None, ge=1),
):
    return controller.list_services(category_id)
