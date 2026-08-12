from pydantic import BaseModel


class ServiceCategoryResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None


class ServiceResponse(BaseModel):
    id: int
    category_id: int
    category_code: str
    category_name: str
    code: str
    name: str
    description: str | None


class ServiceListResponse(BaseModel):
    items: list[ServiceResponse]
    total: int
