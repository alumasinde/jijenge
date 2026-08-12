from app.Modules.Notifications.Repositories.notification_repository import NotificationRepository


class NotificationDispatcher:
    """
    Application-level notification dispatcher.

    Domain services call this only after a state change has successfully
    committed. Phase 7 stores the in-app notification immediately and creates
    an IN_APP delivery record. External SMS/email/push delivery can consume
    notification_deliveries later without changing domain modules.
    """

    def __init__(self):
        self.repository = NotificationRepository()

    def send(
        self,
        recipient_user_id: int,
        notification_type: str,
        title: str,
        body: str,
        entity_type: str | None = None,
        entity_id: int | None = None,
        data: dict | None = None,
    ) -> int:
        return self.repository.create(
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
        )
