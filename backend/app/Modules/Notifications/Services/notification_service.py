from fastapi import HTTPException

from app.Modules.Notifications.Repositories.notification_repository import NotificationRepository
from app.Modules.Notifications.schema import (
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
    RegisterDeviceTokenRequest,
)


class NotificationService:
    def __init__(self):
        self.repository = NotificationRepository()

    def _response(self, row):
        import json

        data = row["data_json"]
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                data = None

        return NotificationResponse(
            id=int(row["id"]),
            notification_type=row["notification_type"],
            title=row["title"],
            body=row["body"],
            entity_type=row["entity_type"],
            entity_id=int(row["entity_id"]) if row["entity_id"] is not None else None,
            data=data,
            read_at=row["read_at"],
            created_at=row["created_at"],
        )

    def list_for_user(self, user_id: int, limit: int, offset: int):
        rows, total, unread_count = self.repository.list_for_user(
            user_id, limit, offset
        )
        return NotificationListResponse(
            items=[self._response(row) for row in rows],
            total=total,
            unread_count=unread_count,
        )

    def mark_read(self, user_id: int, notification_id: int):
        if not self.repository.mark_read(user_id, notification_id):
            raise HTTPException(status_code=404, detail="Notification not found")
        return MarkReadResponse(success=True)

    def mark_all_read(self, user_id: int):
        self.repository.mark_all_read(user_id)
        return MarkReadResponse(success=True)

    def register_device(self, user_id: int, data: RegisterDeviceTokenRequest):
        self.repository.register_device(
            user_id,
            data.platform,
            data.token,
            data.device_name,
            data.app_version,
        )
        return {"success": True}

    def deactivate_device(self, user_id: int, token: str):
        if not self.repository.deactivate_device(user_id, token):
            raise HTTPException(status_code=404, detail="Device token not found")
        return {"success": True}
