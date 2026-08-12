from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    id: int
    category_id: int
    category_code: str
    category_name: str
    code: str
    name: str
    description: str | None
