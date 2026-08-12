from dataclasses import dataclass


@dataclass(frozen=True)
class Notification:
    id: int
    recipient_user_id: int
    notification_type: str
    title: str
    body: str
    entity_type: str | None
    entity_id: int | None
    read_at: object | None
    created_at: object
