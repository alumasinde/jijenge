from fastapi import APIRouter, Depends, Query, Request, status

from app.Core.auth import AuthenticatedUser, require_role
from app.Core.rate_limit import enforce_rate_limit
from app.config import settings
from app.Modules.PublicContent.Controllers.public_content_controller import PublicContentController
from app.Modules.PublicContent.schema import PublicContentResponse, PublicContentWriteRequest

router = APIRouter(tags=["Public content"])
controller = PublicContentController()


@router.get("/public/content")
def get_public_content(locale: str = Query(default="en-KE", min_length=2, max_length=20)):
    items = controller.get_public(locale)
    return {"locale": locale, "items": items}


@router.get("/admin/public-content", response_model=list[PublicContentResponse])
def list_public_content(
    locale: str | None = Query(default=None, max_length=20),
    active_only: bool = False,
    search: str | None = Query(default=None, max_length=160),
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    return controller.list_admin(locale, active_only, search)


@router.post("/admin/public-content", response_model=PublicContentResponse, status_code=status.HTTP_201_CREATED)
def create_public_content(
    request: Request,
    data: PublicContentWriteRequest,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(request, "public-content:create", settings.auth_rate_limit_per_minute)
    return controller.create(data)


@router.put("/admin/public-content/{content_id}", response_model=PublicContentResponse)
def update_public_content(
    content_id: int,
    request: Request,
    data: PublicContentWriteRequest,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(request, "public-content:update", settings.auth_rate_limit_per_minute)
    return controller.update(content_id, data)


@router.delete("/admin/public-content/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_public_content(
    content_id: int,
    request: Request,
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
):
    enforce_rate_limit(request, "public-content:delete", settings.auth_rate_limit_per_minute)
    controller.delete(content_id)
